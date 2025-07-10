from odoo import models, fields


class load_payment_term(models.Model):
    _name = "load.payment.term"
    _description = 'Frecuencia de Facturación'

    name = fields.Text(string = 'Razón o comentario', required=True)
    type_freq = fields.Selection([('daily', 'Diario'), ('week', 'Semanal'), ('fortnight', 'Quincenal'), ('monthly', 'Mensual')], 'Tipo de Sequencia')