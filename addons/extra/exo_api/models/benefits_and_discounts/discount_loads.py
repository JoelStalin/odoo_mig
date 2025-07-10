from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta
import requests
import os
import logging

_logger = logging.getLogger(__name__)


class DiscountLoad(models.Model):
    _name = "discount.load"
    _description = "Descuentos por Carga"

    name = fields.Char(string="Referencia", compute="_compute_name", store=True)
    load_reference_id = fields.Char(string="ID de la Carga", required=True)
    load_external_id = fields.Char(string="ID Externo de la Carga", readonly=True)
    load_number = fields.Char(string="Número de Carga", readonly=True)
    product_quantity = fields.Integer(string="Cantidad", default=1, required=True)
    amount = fields.Float(string="Monto del Descuento", required=True, default=0.0)
    discount_parameters_ids = fields.Many2one(
        "discount.parameters", string="Descuento", required=True, ondelete="cascade"
    )
    discount_ids = fields.One2many(
        'unique.benefit.discount',
        'load_id',
        string="Descuentos Variables"
    )
    discoun_monthly_ids = fields.Many2many("partner.benefit.discount", string="Descuentos Fijos")
    
    imported = fields.Boolean(string="Importado", default=False)

    # Fields for transporter information
    transporter_external_id = fields.Char(string="ID Externo Transportista", readonly=True)
    transporter_name = fields.Char(string="Nombre Transportista", readonly=True)
    transporter_partner_id = fields.Many2one(
        'res.partner',
        string="Transportista (Odoo)",
        domain=[('internal_partner_type', '=', 'transporter')], # Assuming 'internal_partner_type' is a custom field for categorizing partners
        readonly=True,
        help="Linked Odoo partner record for the transporter fetched from the external API."
    )

    @api.depends("load_reference_id", "discount_parameters_ids", "transporter_name")
    def _compute_name(self):
        """
        Computes the name of the discount load record based on the load reference ID,
        the name of the associated discount parameters, and the transporter name.
        """
        for record in self:
            ref = record.load_reference_id or ""
            suffix = f"/{record.discount_parameters_ids.name}" if record.discount_parameters_ids else ""
            transporter_info = f" ({record.transporter_name})" if record.transporter_name else ""
            record.name = f"{ref}{suffix}{transporter_info}"

    def _fetch_and_validate_transporter(self, load_reference_id):
        """
        Helper method to fetch load details from EXO API, extract transporter info,
        and validate against Odoo's res.partner and res.partner.object models.
        Returns a dictionary with 'load_external_id', 'load_number', 'transporter_external_id',
        'transporter_name', and 'transporter_partner_id'.
        Raises ValidationError if any issues occur.
        """
        api_key = os.getenv("EXO_API_KEY")
        exo_api_url = os.getenv("EXO_API_URL")
      
        if not api_key or not exo_api_url:
            raise ValidationError("Faltan las variables de entorno EXO_API_KEY o exo_api_url.")

        if not load_reference_id:
            return {
                'load_external_id': False,
                'load_number': False,
                'transporter_external_id': False,
                'transporter_name': False,
                'transporter_partner_id': False,
            }

        try:
            url = f"{exo_api_url}/exo/fetchLoadByLoadNumber"
            payload = {"loadNumber": f"{load_reference_id}"}
            headers = {
                "Content-Type": "application/json",
                "api-key": api_key,
            }
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
                                      
            result = response.json()
            data = result.get("Result", result)

            fetched_load_external_id = data.get("_id")
            fetched_load_number = data.get("loadNumber")

            if not fetched_load_external_id or not fetched_load_number:
                raise ValidationError("La carga no contiene datos válidos.")

            transporter_data = data.get("vehicle_id", {}).get("transporter_id", {})
            transporter_external_id_api = transporter_data.get("_id")
            transporter_company_name_api = transporter_data.get("company_name")

            if not transporter_external_id_api or not transporter_company_name_api:
                raise ValidationError("No se pudo obtener la información completa del transportista desde la API externa (ID o nombre de la empresa).")

            # Direct search for res.partner using internal_partner_type and partner_object_ids.name
            partner_obj = self.env['res.partner']
            
            existing_partner = partner_obj.search([
                ('internal_partner_type', '=', 'transporter'),
                ('partner_object_ids.name', '=', transporter_external_id_api) 
            ], limit=1)

            if not existing_partner:
                raise ValidationError(
                    f"El transportista con ID externo '{transporter_external_id_api}' "
                    f"no se encontró o no está correctamente vinculado a un socio transportista en Odoo. "
                    "Por favor, asegúrese de que el socio exista y tenga el ID externo configurado en 'Res Partner Object Id'."
                )
            
            # If a partner is found, verify its properties
            if not existing_partner.is_company:
                raise ValidationError(
                    f"El socio encontrado para el ID externo '{transporter_external_id_api}' "
                    f"no está marcado como una compañía en Odoo."
                )
            
            # Additionally, check if the company name matches (optional, for consistency)
            if existing_partner.name != transporter_company_name_api:
                 _logger.warning(
                    f"El nombre del socio en Odoo '{existing_partner.name}' no coincide "
                    f"con el nombre del transportista de la API '{transporter_company_name_api}' "
                    f"para el ID externo '{transporter_external_id_api}'. Usando el socio de Odoo."
                )

            return {
                'load_external_id': fetched_load_external_id,
                'load_number': fetched_load_number,
                'transporter_external_id': transporter_external_id_api,
                'transporter_name': transporter_company_name_api,
                'transporter_partner_id': existing_partner.id,
            }

        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Error al validar la carga: {str(e)}")
        except ValueError as e:
            raise ValidationError(f"Error al procesar la respuesta de la API: {str(e)}")

    @api.onchange("load_reference_id")
    def _onchange_load_reference_id(self):
        """
        Updates fields on the form based on load_reference_id.
        This is for UI interaction and provides immediate feedback.
        """
        result = self._fetch_and_validate_transporter(self.load_reference_id)
        self.load_external_id = result.get('load_external_id')
        self.load_number = result.get('load_number')
        self.transporter_external_id = result.get('transporter_external_id')
        self.transporter_name = result.get('transporter_name')
        self.transporter_partner_id = result.get('transporter_partner_id')

    @api.model
    def create(self, vals):
        """
        Overrides the create method to ensure transporter information is validated
        and populated before the record is saved and discounts are generated.
        """
        # Call the helper to fetch and validate transporter details based on load_reference_id
        if 'load_reference_id' in vals:
            processed_data = self._fetch_and_validate_transporter(vals['load_reference_id'])
            vals['load_external_id'] = processed_data.get('load_external_id')
            vals['load_number'] = processed_data.get('load_number')
            vals['transporter_external_id'] = processed_data.get('transporter_external_id')
            vals['transporter_name'] = processed_data.get('transporter_name')
            vals['transporter_partner_id'] = processed_data.get('transporter_partner_id')
        else:
            # If load_reference_id is not provided (shouldn't happen if required=True),
            # ensure related fields are cleared.
            vals['load_external_id'] = False
            vals['load_number'] = False
            vals['transporter_external_id'] = False
            vals['transporter_name'] = False
            vals['transporter_partner_id'] = False
            # Consider raising a ValidationError here if load_reference_id is strictly required on create

        vals["imported"] = self.env.context.get("import_file", False)
        record = super().create(vals) # The record is created with populated transporter_partner_id

        if vals["imported"]:
            record.action_generate_discounts()
        else:
            record._create_discount_record()
        return record

    def write(self, vals):
        """
        Overrides the write method to ensure transporter information is validated
        and updated if load_reference_id changes.
        """
        if 'load_reference_id' in vals:
            # If load_reference_id is being changed, re-fetch and validate transporter details
            processed_data = self._fetch_and_validate_transporter(vals['load_reference_id'])
            vals['load_external_id'] = processed_data.get('load_external_id')
            vals['load_number'] = processed_data.get('load_number')
            vals['transporter_external_id'] = processed_data.get('transporter_external_id')
            vals['transporter_name'] = processed_data.get('transporter_name')
            vals['transporter_partner_id'] = processed_data.get('transporter_partner_id')

        res = super().write(vals)

        # Re-generate discounts if certain fields change, or if it's an import triggered write
        # This part depends on your exact business logic for updates and imports.
        # If 'imported' is set to True via write (e.g. during an import process),
        # or if the user clicks a 'generate discounts' button which triggers a write.
        # For simplicity, we'll assume action_generate_discounts handles its own trigger.
        # If record was newly created via import (imported=True in vals from create method),
        # the action_generate_discounts was already called in create.
        # This part of 'write' is more for re-calculating on manual changes,
        # or if 'imported' field is changed after creation.
        # For this specific error, the primary fix is in 'create'.
        
        # You might want to re-call _create_discount_record only if relevant fields changed
        # or if it's a specific action. For now, this is outside the scope of the original error.

        return res


    def _create_discount_vals(self):
        """
        Generates a list of dictionaries with values for creating discount records.
        Distinguishes between 'one_time' and 'monthly' frequencies based on
        discount parameters.
        Includes the 'amount' and 'transporter_partner_id'.
        """
        self.ensure_one()
        params = self.discount_parameters_ids
        if not params:
            return []

        # Ensure transporter_partner_id is available before proceeding
        if not self.transporter_partner_id:
            raise ValidationError("No se pudo asignar el transportista. Por favor, verifique la carga y el transportista asociado.")

        common_vals = {
            "name": self.name,
            "product_quantity": self.product_quantity,
            "load_id": self.id,
            "amount": self.amount,  # Use the 'amount' field from discount.load
            "partner_id": self.transporter_partner_id.id, # Link the Odoo partner
        }

        if params.frequency == "one_time":
            return [{
                **common_vals,
                "product_tmpl_id": params.product_tmpl_id.id,
                "transaction_type": params.transaction_type,
                "analytic_account_id": params.analytic_account_id.id,
            }]
        elif params.frequency == "monthly":
            # Search for an existing cycle or create a default one
            cicle = self.env["benefit.discount.cicle"].search([], limit=1)
            if not cicle:
                next_month = date.today() + timedelta(days=30)
                cicle = self.env["benefit.discount.cicle"].create({
                    "name": "Default Cycle",
                    "next_curt_date": date(next_month.year, next_month.month, 1),
                })

            # Search for an existing benefit discount or create a new one
            discount = self.env["benefit.discount"].search([
                ("product_tmpl_id", "=", params.product_tmpl_id.id)
            ], limit=1)

            if not discount:
                discount = self.env["benefit.discount"].create({
                    "product_tmpl_id": params.product_tmpl_id.id,
                    "name": f"Descuento por {params.product_tmpl_id.name}",
                    "origin": "odoo",
                    "benefit_discount_cicles_ids": [(6, 0, [cicle.id])],
                })
            
            return [{
                **common_vals,
                "benefit_discount_id": discount.id,
                "analytic_account_id": params.analytic_account_id.id,
            }]
        return [] # Return empty list if frequency is not recognized

    def _create_discount_record(self):
        """
        Creates discount records based on the discount parameters associated with the load.
        Ensures uniqueness for generated discounts based on load_id and discount type/parameters.
        """
        for record in self:
            discount_vals_list = record._create_discount_vals()
            if not discount_vals_list:
                continue

            for discount_vals in discount_vals_list:
                model = "unique.benefit.discount" if record.discount_parameters_ids.frequency == "one_time" else "partner.benefit.discount"
                domain = [('load_id', '=', record.id)] # Always link to the specific load

                if model == "unique.benefit.discount":
                    domain.extend([
                        ("product_tmpl_id", "=", record.discount_parameters_ids.product_tmpl_id.id),
                        ("transaction_date", "=", date.today()), # Assuming transaction_date is always today for one-time
                        # Optionally, add partner_id to domain if multiple discounts for different partners on same load are allowed
                        # ("partner_id", "=", record.transporter_partner_id.id) 
                    ])
                else: # partner.benefit.discount (monthly)
                    domain.extend([
                        ("benefit_discount_id", "=", discount_vals['benefit_discount_id']),
                        # Optionally, add partner_id to domain if multiple monthly discounts for different partners on same load are allowed
                        # ("partner_id", "=", record.transporter_partner_id.id)
                    ])

                existing_discount = self.env[model].search(domain, limit=1)
                if existing_discount:
                    _logger.warning(
                        f"Ya existe un descuento de tipo '{model}' para esta carga "
                        f"con los parámetros especificados. No se creará un duplicado."
                    )
                    continue

                # Create the new discount record
                self.env[model].create(discount_vals)

    def action_generate_discounts(self):
        """
        Action method to manually trigger the generation of discount records.
        Resets the 'imported' flag after generation.
        """
        for record in self:
            # Ensure transporter_partner_id is set before generating discounts
            if not record.transporter_partner_id and record.load_reference_id:
                try:
                    processed_data = record._fetch_and_validate_transporter(record.load_reference_id)
                    record.write({
                        'load_external_id': processed_data.get('load_external_id'),
                        'load_number': processed_data.get('load_number'),
                        'transporter_external_id': processed_data.get('transporter_external_id'),
                        'transporter_name': processed_data.get('transporter_name'),
                        'transporter_partner_id': processed_data.get('transporter_partner_id'),
                    })
                except ValidationError as e:
                    _logger.error(f"Error validating transporter during action_generate_discounts: {e.name}")
                    raise # Re-raise to show the error to the user


            record._create_discount_record()
            record.imported = False

    @api.onchange("product_quantity")
    def _onchange_product_quantity(self):
        """
        Updates the product quantity on related discount records when the
        product_quantity of the discount.load changes.
        """
        for rec in self:
            if rec.discount_ids:
                rec.discount_ids.write({"product_quantity": rec.product_quantity})
            if rec.discoun_monthly_ids:
                rec.discoun_monthly_ids.write({"product_quantity": rec.product_quantity})

