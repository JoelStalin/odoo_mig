from odoo import _, api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    payment_to = fields.Many2one("res.partner", string=_("Pagar a"))

    @api.onchange("payment_to")
    def _onchange_paymento_to(self):
        for invoice in self:
            if invoice.is_invoice(include_receipts=True) and invoice.payment_to:
                inv = invoice._origin or invoice
                line = inv.line_ids.filtered(
                    lambda l: l.account_id.user_type_id.type == "payable"
                )
                if line:
                    line.partner_id = invoice.payment_to

    def _recompute_dynamic_lines(
        self, recompute_all_taxes=False, recompute_tax_base_amount=False
    ):
        super()._recompute_dynamic_lines(recompute_all_taxes, recompute_tax_base_amount)

        self._onchange_paymento_to()

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        # Esto es necesario ya que account/models/account_move.py linea 3014 a 3019
        # remodifica el campo partner de la linea.
        self._onchange_paymento_to()
        return res
