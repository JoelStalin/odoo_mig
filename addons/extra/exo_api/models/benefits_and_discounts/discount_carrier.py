from odoo import models, fields, api
from datetime import date, timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class DiscountCarrier(models.Model):
    _name = "discount.carrier"
    _description = "Descuentos por Transportista"
    _sql_constraints = [
        (
            "fuel_card_unique",
            "unique(fuel_card)",
            "La tarjeta de combustible debe ser única.",
        )
    ]

    name = fields.Char(compute="_compute_name", string="Razon", required=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        domain=[("internal_partner_type", "=", "transporter")],
        required=True,
    )
    product_quantity = fields.Integer(string="Cantidad", default=1, required=True)
    discount_parameters_ids = fields.Many2one(
        "discount.parameters", string="Descuento", required=True, ondelete="cascade"
    )
    discount_ids = fields.One2many(
        "unique.benefit.discount",
        "carrier_ids",
        string="Descuentos Variables",
        # ondelete="cascade",
    )
    discoun_monthly_ids = fields.One2many(
        "partner.benefit.discount",
        "carrier_ids",
        string="Descuentos Fijos y Recurrentes",
        # ondelete="cascade",
    )
    imported = fields.Boolean(string="Importado", default=False)
    fuel_card = fields.Char(string="Tarjeta de Combustible", required=False)
    is_combustible = fields.Boolean(
        string="Es Combustible", compute="_compute_is_combustible"
    )

    _sql_constraints = [
        (
            "fuel_card_unique",
            "unique(fuel_card)",
            "La tarjeta de combustible debe ser única.",
        )
    ]

    @api.onchange("is_combustible")
    def _onchange_is_combustible(self):
        if self.is_combustible:
            self._fields["fuel_card"].required = self.is_combustible

    @api.depends("discount_parameters_ids")
    def _compute_is_combustible(self):
        for record in self:
            if (
                record.discount_parameters_ids
                and record.discount_parameters_ids.product_tmpl_id
            ):
                record.is_combustible = (
                    record.discount_parameters_ids.product_tmpl_id.barcode
                    == "COMBUSTIBLE"
                )
            else:
                record.is_combustible = False

    @api.depends("partner_id", "discount_parameters_ids")
    def _compute_name(self):
        for record in self:
            record.name = (
                f"{record.partner_id.name}/{record.discount_parameters_ids.name}"
            )

    @api.model
    def create(self, vals):
        is_importing = self.env.context.get("import_file", False)
        vals["imported"] = is_importing
        record = super().create(vals)
        if record.is_combustible != True:
            if is_importing:
                record.action_generate_discounts()
            else:
                record._create_discount_record()
        return record

    def _create_discount_vals(self):
        self.ensure_one()
        if not self.discount_parameters_ids:
            return

        params = self.discount_parameters_ids
        common_vals = {
            "name": self.name,
            "partner_id": self.partner_id.id,
            "product_quantity": self.product_quantity,
            "carrier_ids": self.id,
        }

        if params.frequency == "one_time":
            return [
                {
                    **common_vals,
                    "amount": params.amount,
                    "product_tmpl_id": params.product_tmpl_id.id,
                    "transaction_type": params.transaction_type,
                    "analytic_account_id": params.analytic_account_id.id,
                }
            ]
        elif params.frequency == "monthly":
            cicle = self.env["benefit.discount.cicle"].search([], limit=1)
            if not cicle:
                next_month_date = date.today() + timedelta(days=30)
                first_day_next_month = date(
                    next_month_date.year, next_month_date.month, 1
                )
                cicle = self.env["benefit.discount.cicle"].create(
                    {
                        "name": "Default Cycle",
                        "next_curt_date": first_day_next_month,
                    }
                )
            discount = self.env["benefit.discount"].search(
                [("product_tmpl_id", "=", params.product_tmpl_id.id)], limit=1
            )
            if not discount:
                discount = self.env["benefit.discount"].create(
                    {
                        "product_tmpl_id": params.product_tmpl_id.id,
                        "name": f"Descuento Por {params.product_tmpl_id.name}",
                        "origin": "odoo",
                        "benefit_discount_cicles_ids": [(6, 0, [cicle.id])],
                    }
                )

            return [
                {
                    **common_vals,
                    "benefit_discount_id": discount.id,
                    "analytic_account_id": params.analytic_account_id.id,
                }
            ]

        return

    def _create_discount_record(self):
        for record in self:
            discount_vals = record._create_discount_vals()
            if discount_vals:
                model = (
                    "unique.benefit.discount"
                    if record.discount_parameters_ids.frequency == "one_time"
                    else "partner.benefit.discount"
                )
                if record.discount_parameters_ids.frequency == "one_time":
                    existing_discount = self.env[model].search(
                        [
                            ("partner_id", "=", record.partner_id.id),
                            (
                                "product_tmpl_id",
                                "=",
                                record.discount_parameters_ids.product_tmpl_id.id,
                            ),
                            ("transaction_date", "=", date.today()),
                        ],
                        limit=1,
                    )
                    if existing_discount:
                        _logger.warning(
                            "Ya existe un descuento para este cliente con la fecha de transacción de hoy"
                        )
                        continue
                    else:
                        self.env[model].create(discount_vals)
                else:
                    existing_discount = self.env[model].search(
                        [
                            ("partner_id", "=", record.partner_id.id),
                            (
                                "benefit_discount_id",
                                "=",
                                discount_vals[0]["benefit_discount_id"],
                            ),
                        ],
                        limit=1,
                    )
                    if existing_discount:
                        _logger.warning("Ya existe un descuento para este cliente")
                        continue
                    self.env[model].create(discount_vals)

    def action_generate_discounts(self):
        for record in self:
            record._create_discount_record()
            record.write({"imported": False})

    @api.onchange("product_quantity")
    def _onchange_product_quantity(self):
        if self.product_quantity:
            for discount in self.discount_ids:
                discount.product_quantity = self.product_quantity
                discount.write({"product_quantity": self.product_quantity})
            for discount in self.discoun_monthly_ids:
                discount.product_quantity = self.product_quantity
                discount.write({"product_quantity": self.product_quantity})
