from odoo import models, fields
from odoo.exceptions import ValidationError

class PortalMixinInherit(models.AbstractModel):
    _inherit = 'portal.mixin'

    def get_invoice_url(self, state):
        return f"/api/account/move/{self.id}/state/{state}/"
    
    def get_back(self):
        return f"/api/my/invoices/"