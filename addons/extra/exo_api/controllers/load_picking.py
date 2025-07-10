from odoo import http
from odoo.http import request
import json


class OrderAPIController(http.Controller):

    # ✅ Endpoint para recibir la carga y crear la orden en estado draft
    @http.route(
        "/api/create_order", type="json", auth="public", methods=["POST"], csrf=False
    )
    def create_order(self, **post):
        try:
            data = post.get("data")
            if not data:
                return {"status": "error", "message": "Missing data"}

            # Obtener datos del shipper
            shipper = data.get("shipper_info", {})
            customer = shipper.get("customer", "")
            rnc = shipper.get("rnc", "")

            # Obtener datos del cliente final
            end_client = data.get("end_client_info", {})
            client_name = end_client.get("client_name", "")
            client_address = end_client.get("client_address", "")
            client_city = end_client.get("client_city", "")
            client_province = end_client.get("client_province", "")
            client_zip_code = end_client.get("client_zip_code", "")

            # Obtener datos de la orden
            order_info = data.get("order_info", {})
            order_id = order_info.get("order_id", "")
            service_type = order_info.get("service_type", "")
            expected_date = order_info.get("expected_date", "")
            expected_time = order_info.get("expected_time", "")

            # ✅ Obtener productos
            products = data.get("product_info", [])

            # ✅ Crear partner (si no existe)
            partner = (
                request.env["res.partner"]
                .sudo()
                .search([("name", "=", client_name)], limit=1)
            )
            if not partner:
                partner = (
                    request.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": client_name,
                            "street": client_address,
                            "city": client_city,
                            "state_id": request.env["res.country.state"]
                            .search([("name", "=", client_province)], limit=1)
                            .id,
                            "zip": client_zip_code,
                            "country_id": request.env["res.country"]
                            .search([("code", "=", "DO")], limit=1)
                            .id,
                        }
                    )
                )

            created_pickings = []

            # ✅ Crear órdenes de entrada para cada almacén
            for product in products:
                warehouse_name = product.get("warehouse", "")
                quantity = product.get("quantity", 0)
                unit_weight = product.get("unit_weight", 0)
                serial_number = product.get("serial_number", "")
                lot_name = product.get("lot_name", "")

                # ✅ Buscar almacén
                warehouse = (
                    request.env["stock.warehouse"]
                    .sudo()
                    .search([("name", "=", warehouse_name)], limit=1)
                )
                # if not warehouse:
                #     return {'status': 'error', 'message': f'Almacén "{warehouse_name}" no encontrado'} #🧑‍⚖️ Por orden de Luis

                # ✅ Buscar tipo de picking para el almacén
                picking_type = (
                    request.env["stock.picking.type"]
                    .sudo()
                    .search(
                        [
                            ("warehouse_id", "=", warehouse.id),
                            ("code", "=", "incoming"),
                        ],
                        limit=1,
                    )
                )

                if not picking_type:
                    return {
                        "status": "error",
                        "message": f"No se encontró un tipo de picking para el almacén {warehouse_name}",
                    }

                # ✅ Crear orden de entrada en estado "draft"
                picking = (
                    request.env["stock.picking"]
                    .sudo()
                    .create(
                        {
                            "partner_id": partner.id,
                            "picking_type_id": picking_type.id,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": picking_type.default_location_dest_id.id,
                            "scheduled_date": f"{expected_date} {expected_time}",
                            "origin": order_id,
                            "note": f"Servicio: {service_type}",
                            "state": "draft",  # Crear en estado 'draft'
                        }
                    )
                )

                # ✅ Buscar o crear el producto
                product_template = (
                    request.env["product.product"]
                    .sudo()
                    .search([("default_code", "=", product.get("name", ""))], limit=1)
                )

                if not product_template:
                    product_template = (
                        request.env["product.product"]
                        .sudo()
                        .create(
                            {
                                "name": product.get("product_description", ""),
                                "default_code": product.get("name", ""),
                                "weight": unit_weight,
                                "type": "product",
                                "tracking": (
                                    "lot"
                                    if lot_name
                                    else "serial" if serial_number else "none"
                                ),
                            }
                        )
                    )

                # ✅ Crear lote o serial
                lot_id = False
                if lot_name:
                    lot_id = (
                        request.env["stock.production.lot"]
                        .sudo()
                        .create({"name": lot_name, "product_id": product_template.id})
                    )
                elif serial_number:
                    lot_id = (
                        request.env["stock.production.lot"]
                        .sudo()
                        .create(
                            {"name": serial_number, "product_id": product_template.id}
                        )
                    )

                # ✅ Crear movimiento de stock
                stock_move = (
                    request.env["stock.move"]
                    .sudo()
                    .create(
                        {
                            "picking_id": picking.id,
                            "product_id": product_template.id,
                            "name": product_template.name,
                            "product_uom_qty": quantity,
                            "product_uom": product_template.uom_id.id,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": picking_type.default_location_dest_id.id,
                        }
                    )
                )

                # ✅ Asignar lote o serial al movimiento
                if lot_id:
                    request.env["stock.move.line"].sudo().create(
                        {
                            "move_id": stock_move.id,
                            "product_id": product_template.id,
                            "qty_done": quantity,
                            "lot_id": lot_id.id,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": picking_type.default_location_dest_id.id,
                        }
                    )

                created_pickings.append(picking.name)

            return {
                "status": "success",
                "message": f"Órdenes creadas en estado draft: {', '.join(created_pickings)}",
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ✅ Endpoint para actualizar el estado de la orden
    @http.route(
        "/api/update_order_status",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def update_order_status(self, **post):
        try:
            order_id = post.get("order_id")
            new_status = post.get("new_status")

            if not order_id or not new_status:
                return {"status": "error", "message": "Faltan datos requeridos"}

            picking = (
                request.env["stock.picking"]
                .sudo()
                .search([("name", "=", order_id)], limit=1)
            )
            if not picking:
                return {"status": "error", "message": f"Orden {order_id} no encontrada"}

            if new_status.lower() == "done":
                picking.button_validate()
            elif new_status.lower() == "cancel":
                picking.action_cancel()
            elif new_status.lower() == "confirm":
                picking.action_confirm()
            elif new_status.lower() == "draft":
                picking.write({"state": "draft"})
            else:
                return {"status": "error", "message": f"Estado {new_status} no válido"}

            return {
                "status": "success",
                "message": f"Estado de orden {order_id} actualizado a {new_status}",
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
