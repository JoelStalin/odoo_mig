from odoo import models, fields
from datetime import datetime, date

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

class employee_inherit(models.Model):
    _inherit = "hr.employee"

    working_time_in_months = fields.Integer(compute='_compute_working_time', string='Meses Laborando')
    
    def _compute_working_time(self):
        today = date.today()
        for record in self:
            total_months = diff_month(today, record.first_contract_date)
            record.working_time_in_months = total_months if total_months <= 12 else 12
            

            
    
    