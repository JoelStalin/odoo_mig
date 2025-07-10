from odoo import _,  models, fields
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import date
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)
class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"
    load_numbers = fields.Char(string = 'Número de Cargas', compute="_compute_load_numbers")
    load_group_key = fields.Char(string = 'Clave de agrupacion de carga', tracking=True)

    load_ids = fields.One2many('account.line.load', 'account_line_id', 'Cargas', help="Obtiene las cargas de exo asociada a esta linea de factura.",  
                            #    ondelete='cascade'
                               )
    load_qty = fields.Integer('Numero de Cargas', compute="_compute_load_qty")
    is_automatic_line = fields.Boolean('Es una linea de una factura automatica?', default = False, required = True, tracking=True)
    benefit_discount_id = fields.Many2one('benefit.discount', 'Beneficios y/o descuentos', tracking=True)
    benefit_discount_cicle_id = fields.Many2one('benefit.discount.cicle', 'Ciclo del Descuento', tracking=True)
    unique_benefit_discounts = fields.One2many('unique.benefit.discount', 'move_line_id', 'Descuentos Unicos', help="Listado de descuentos unicos.", tracking=True)
    line_type = fields.Char("Tipo de Linea", default="Normal", tracking=True)
    

    def _compute_load_qty(self):
        for move_line in self:
            move_line.load_qty = len(move_line['load_ids']) if move_line['load_ids'] else 0
    
    def _compute_load_numbers(self):
        for move_line in self:
            loads = []
            for load in  move_line.load_ids.sorted(lambda x: x.load_number):
                loads.append(load['load_number'])
            
            move_line.load_numbers = ','.join(loads)