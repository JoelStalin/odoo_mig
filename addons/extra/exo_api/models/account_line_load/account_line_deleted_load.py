from odoo import models, fields
from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class account_line_deleted_load(models.Model):
    _name = "account.line.deleted.load"
    _description = 'Load Borradas'

    move_type = fields.Selection([('invoice', 'Factura de un Shipper'), ('bill', 'Factura de un Transportista')], help="Indica si la carga se creo a partir de un factura de un cliente o de una factura de un tranportista")
    driver = fields.Char('Conductor')
    status = fields.Char('Status')
    shipper = fields.Char('Shipper')
    load_id = fields.Char('Id de la Carga')
    load_number = fields.Char('Numero de Carga')
    account_line_id = fields.Char("Linea de Factura a la que pertenecia")
    account_move_id = fields.Char("Factura a la que perteneceia")
    orders = fields.Char('Ordenes')
    json_current_load = fields.Text('Json de la carga con el cual se creó este registro', default= '{}')
    would_be_in_move_line_id = fields.Many2one('account.move.line',  string="Linea probable donde deberia estar")

    def create_deleted(self, account_lines_loads):
        for record in account_lines_loads:
            item = {
                'move_type': record.move_type,
                'driver': record.driver,
                'status': record.status,
                'shipper': record.shipper,
                'load_id': record.load_id,
                'load_number': record.load_number,
                'account_line_id': f"{record.account_line_id.id} - {record.account_line_id.name}" if record.account_line_id else False,
                'account_move_id': f"{record.account_move_id.id} - {record.account_move_id.name}" if record.account_move_id else False,
                'orders': record.orders,
                'json_current_load': record.json_current_load,
            }
            self.sudo().create(item)
    
    def action_restore_load(self):
        for record in self:
            if (record.would_be_in_move_line_id):
                self.env['account.line.load'].sudo().create({
                    'load_number': record.load_number,
                    'account_line_id': record.would_be_in_move_line_id.id,
                    'account_move_id': record.would_be_in_move_line_id.move_id,
                    'was_restored': True
                })
                
    def action_set_would_be_in_move_line_id(self):
        for record in self:
            if (record.would_be_in_move_line_id):
                continue
            _logger.info("_______ _compute_would_be_in_move_line_id ______")
            _logger.info(record.account_line_id)
            line_name = record.account_line_id.split('-', 1)[1].strip() if record.account_line_id else None
            _logger.info(line_name)
            if (line_name):
                move_type = 'out_invoice' if record.move_type == 'invoice' else 'in_invoice'
                _logger.info(move_type)
                start_date = record.create_date - relativedelta(days=30)
                end_date = record.create_date + relativedelta(days=30)
                move_line = self.env['account.move.line'].sudo().search([
                    ('create_date', '>=', start_date),
                    ('create_date', '<=', end_date),
                    
                    ('load_ids', '=', False), ('move_id.move_type', '=', move_type ), ('name', '=', line_name)])
                _logger.info(move_line)
                if (len(move_line) > 1):
                    _logger.info(line_name)
                    _logger.info(len(move_line))
                    continue
                if (move_line):
                    record.would_be_in_move_line_id = move_line.id
            