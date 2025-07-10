from odoo import _,  models, fields
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import date
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticAccountInherit(models.Model):
    _inherit = "account.analytic.account"

    warehouses = fields.One2many('account.analytic.warehouse', 'analytic_account_id', string="Warehouses")

    is_to_invoice = fields.Boolean('Es para factura automatica?', default = True)
