from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

class DrivesClientItem(models.Model):
    _name = 'drive.item'
    _description = 'Registro de conduces de un cliente'
    
    name = fields.Char("Conduce", required=True)
    drives_client_id = fields.Many2one('drives.client', 'Drive client', required=True, ondelete="cascade")
    active = fields.Boolean(default=True)

class DrivesClient(models.Model):
    _name = 'drives.client'
    _description = 'Conduces de un cliente'
    
    partner_id = fields.Many2one('res.partner', 'Shipper', required=True)
    drives = fields.One2many('drive.item', 'drives_client_id', string='Conduces')
    active = fields.Boolean(default=True)
    
    def name_get(self):
        result = []
        for record in self:
            drive_names = [drive.name for drive in record.drives]
            drives_str = ", ".join(drive_names)
            result.append((record.id, f"{record.partner_id.name} ({drives_str})"))

        return result





