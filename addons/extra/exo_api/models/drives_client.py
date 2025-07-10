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
    _rec_name = 'display_name'

    partner_id = fields.Many2one('res.partner', 'Shipper', required=True)
    drives = fields.One2many('drive.item', 'drives_client_id', string='Conduces')
    active = fields.Boolean(default=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    @api.depends('partner_id', 'partner_id.name', 'drives', 'drives.name')
    def _compute_display_name(self):
        for record in self:
            drive_names = [drive.name for drive in record.drives if drive.name]
            drives_str = ", ".join(drive_names)
            partner_name = record.partner_id.name if record.partner_id else ""
            if drives_str:
                record.display_name = f"{partner_name} ({drives_str})"
            else:
                record.display_name = partner_name





