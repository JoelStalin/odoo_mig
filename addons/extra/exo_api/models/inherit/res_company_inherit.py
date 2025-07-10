from odoo import models, fields
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import datetime


class company_inherit(models.Model):
    _inherit = "res.company"
    
    code = fields.Char("Codigo")
    default_image = fields.Image("Image Por Defecto Transportistas", max_width=1920, max_height=1920)
    company_managers = fields.Many2many('res.users', string='Representantes de la Empresa', check_company=True)
    
    def send_me_notification(self, message_subject, message):
        for company in self:
            if (company.company_managers):
                company.sudo().company_managers.send_message_channel(message_subject, message)
                
                
    _sql_constraints = [
        ('code_uniq', 'unique (code)', "The code must be unique!"),
    ]