from odoo import _, models, fields, api


class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    load_number = fields.Char(string='Número de Carga')

    partner_bank_do_id = fields.Many2one(
        'bank.account.dominicana',
        string='Cuenta Bancaria',
        domain="[('partner_id', '=', partner_id), ('active', '=', True)]",
        help="Cuenta bancaria activa del beneficiario."
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_set_bank_account(self):
        for payment in self:
            if payment.partner_id:
                bank_account = self.env['bank.account.dominicana'].search([
                    ('partner_id', '=', payment.partner_id.id),
                    ('active', '=', True),
                ], limit=1)
                payment.partner_bank_do_id = bank_account or False
            else:
                payment.partner_bank_do_id = False
