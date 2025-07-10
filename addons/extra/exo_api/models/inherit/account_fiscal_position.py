# from ...helpers.request_helper import request_sync
from odoo import models, api, fields

class account_fiscal_position(models.Model):
    _inherit = "account.fiscal.position"
    
    request_l10n_latam_document_number = fields.Boolean("Solicitar el No. Comprobante Fiscal",  help="Solicita a la factura del proveedor el No. Comprobante Fiscal")