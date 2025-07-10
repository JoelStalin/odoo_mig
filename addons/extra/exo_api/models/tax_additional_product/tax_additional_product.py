from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TaxAdditionalProduct(models.Model):
    _name = "tax.additional.product"
    _description = 'Impuestos adicional para los productos'

    name = fields.Text(string = 'Razón o comentario', required=True)
    product_tmpl_id = fields.Many2one('product.template', string="Producto de Referencia", required=True)
    tax_id = fields.Many2one('account.tax', string="Impuesto", required=True)
