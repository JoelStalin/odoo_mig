from odoo import models, fields

class exo_load_configuration_field(models.Model):
    _name = "exo.load.configuration.field"
    _description = 'Campos para la configuracion de cargas de exo'

    load_group_key = fields.Selection([
        ('partner_analytics_accounts', 'Cuentas Analiticas'),
        ('partner_product', 'Producto del Cliente'), ('partner_analytic_tag_ids', 'Etiqueta analítica del cliente'),
        ('target_client', 'Cliente de la Orden'),
        ('order_client_id', 'Id del Cliente de la Orden'),
        
        ('partner_id', 'Cliente en odoo'),
        ('invoicing_date', 'Fecha de Invocing Date'),
         
        ('loadNumber', 'Numero de Carga'),
        ('zone', 'Zona'), ('order_num', 'Order Num'),
        ('vehicle_plate', 'Placa  Vehículo'),
        ('warehouse', 'Almacén'),
        ('order_comment', 'Comentarios de una orden'),

        ('address', 'Direccion'),  ('vehicle_type', 'Tipo de Vehiculo'),
        ('exceptions', 'Excepciones'),  ('products_name', 'Nombre de los productos de una carga')
    ], string='Agrupar por',  help='Indica por que campo se desea agrupar las facturas', required=True)
    configuration_id = fields.Many2one('exo.partner.load.configuration', 'Configuracion', required=True, ondelete='cascade')
