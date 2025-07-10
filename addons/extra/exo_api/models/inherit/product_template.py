from odoo import models

class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Ya existe un producto con el mismo nombre.'),
    ]