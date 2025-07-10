from odoo import models, fields


class BenefitDiscount(models.Model):
    _name = "benefit.discount"
    _description = 'Beneficios y/o descuentos'

    name = fields.Text(string = 'Razón o comentario', required=True)
    origin = fields.Selection([('odoo', 'Odoo')], default='odoo', required=True)
    product_tmpl_id = fields.Many2one('product.template', string="Producto Tipo Debito o Credito", required=True, 
                                      domain=[('type', '=', 'service')],
                                      help="Si necesita que sea débito el Producto/Servicio debe estar en el precio de venta en negativo.")
    
    benefit_discount_cicles_ids = fields.Many2many('benefit.discount.cicle', string="Ciclos", required=True)
    carrier_ids = fields.Many2one('discount.carrier', string="Transportista")
    
 
