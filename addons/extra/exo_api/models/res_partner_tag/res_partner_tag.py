from odoo import models, fields

class res_partner_tag(models.Model):
    _name = "res.partner.tag"
    _description = 'Etiquetas Analíticas de un Contacto'
    
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete='cascade', index=True, required=True)
    analytic_tag_id = fields.Many2one('account.analytic.tag', string='Etiqueta Analítica')

    
    