from odoo import models, fields

class exo_partner_load_configuration(models.Model):
    _name = "exo.partner.load.configuration"
    _description = 'Configuracion de carga de facturas'

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    is_summarized = fields.Boolean("Es sumarizada")
    
    fields = fields.One2many('exo.load.configuration.field', 'configuration_id', 'Campos', help="Define los campos que se visualizaran en la factura del cliente.", required=True)

    def name_get(self):
        result = []
        for record in self:
            text = ''
            for partner in record.partner_id:
                text += ' ' + partner['name']
            result.append((record.id, text))
        return result
