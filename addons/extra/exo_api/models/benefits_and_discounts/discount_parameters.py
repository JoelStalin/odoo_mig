from odoo import models, fields, api

class DiscountParam(models.Model):
    _name = 'discount.parameters'
    _description = 'Parametros de Descuentos'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    active = fields.Boolean(string='Active', default=True)
    product_tmpl_id = fields.Many2one('product.template', string="Producto de Referencia", required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta Analítica", required=True)
    amount = fields.Float("Precio Producto", compute="_compute_amount", store=True, tracking=True)
    transaction_type = fields.Selection([('debit', 'Debito'), ('credit', 'Credito')], string="Tipo de Transacción", default='credit', required=True)
    carrier_ids = fields.One2many('discount.carrier', 'discount_parameters_ids', string='Carriers') 
    frequency = fields.Selection([
        ('one_time', 'De unico uso'),
        ('monthly', 'Mensual'),
        ('biweekly', 'Quincenalmente')
    ], string="Frecuencia", default='one_time', required=True)

    @api.depends('product_tmpl_id', 'product_tmpl_id.list_price')
    def _compute_amount(self):
        """
        Sincroniza el precio del producto de referencia con el campo `amount`
        cada vez que el precio del producto cambie.
        """
        for record in self:
            if record.product_tmpl_id:
                record.amount = record.product_tmpl_id.list_price

    @api.depends('product_tmpl_id')
    def _compute_name(self):
        for record in self:
            record.name = record.product_tmpl_id.name or False
