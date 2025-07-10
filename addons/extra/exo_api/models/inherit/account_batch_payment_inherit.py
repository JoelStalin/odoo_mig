from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    is_approved = fields.Boolean(string="Aprobado por encargado de aprobación", default=False, help="Indica si fue aprobado por el dueño de la empresa o un encargado de aprobación", tracking=True)
    
    def approve_batch_payment(self):
        self.sudo().write({
            'is_approved': True
        })
        
    def validate_batch(self):
        self.ensure_one()
        if not self.is_approved :
            raise UserError("Aun no ha sido aprobado por el Encargado")

        return super(AccountBatchPayment, self).validate_batch()