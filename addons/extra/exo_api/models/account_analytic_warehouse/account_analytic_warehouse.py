from odoo import _,  models, fields
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import date
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticWarehouse(models.Model):
    _name = "account.analytic.warehouse"
    
    name = fields.Char("Warehouse", required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta análitica", readonly=True)