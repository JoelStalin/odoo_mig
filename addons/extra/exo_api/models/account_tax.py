from odoo import _,  models, fields
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import date
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)
class AccountTaxInherit(models.Model):
    _inherit = "account.tax"

    tax_code = fields.Char(string = 'Clave para identificar impuesto')
