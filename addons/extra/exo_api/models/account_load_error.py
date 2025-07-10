from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

class account_load_error(models.Model):
    _name = 'account.load.error'
    _description = 'Errores al obtener una carga para un cliente'
    
    name = fields.Char("Nombre")
    account_load_client_id = fields.Many2one('res.partner', 'Cliente', required=True)
    start_date = fields.Datetime(string='Fecha Inicio', required=True)
    end_date = fields.Datetime(string='Fecha Fin',  required=True)
    current_date  = fields.Datetime(string='Fecha en que sucedió el error', required=True)
    message_error = fields.Text(string='Reason')
    state = fields.Selection([('draft', 'Draft'), ('checked', 'Revisado'), ('closed', 'Cerrado')], 'Status', copy=False, default='draft')
    partner_type = fields.Selection([('Proveedor', 'Proveedor'), ('Shipper', 'Shipper'), ('Interno', 'Interno')], 'Tipo de Contacto', copy=False, default='Proveedor')
    process_uid = fields.Char(string='UID de Proceso', index=True, help='Identificador único de proceso de sincronización')