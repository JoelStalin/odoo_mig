from odoo.exceptions import ValidationError
from odoo import models, fields, http, _, api

import logging
_logger = logging.getLogger(__name__)
class hr_payslip_line_inherit(models.Model):
    _inherit = "hr.payslip.line"

    over_employee_name = fields.Char(string='Empleado', compute='_compute_over_employee_name' )
    over_date_period = fields.Char(string='Periodo', compute='_compute_over_date_from' )
    over_contract_name = fields.Char(string='', compute='_compute_over_contract_name' )
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Batch Name', compute='_compute_payslip_run_id', store=True, index=True, readonly=True)
    salary_rule_name = fields.Char(string='Nombre a mostrar en el excel', compute='_compute_salary_rule_name' )

    @api.depends('slip_id.payslip_run_id')
    def _compute_payslip_run_id(self):
        for record in self:
            record.payslip_run_id = record.slip_id.payslip_run_id

    def _compute_over_employee_name(self):
        for record in self:
            record.over_employee_name = record.slip_id.employee_id.name
    
    def _compute_salary_rule_name(self):
        for record in self:
            record.salary_rule_name = record.salary_rule_id.name

    def _compute_over_date_from(self):
        for record in self:
            record.over_date_period = record.slip_id.date_from.strftime("%B %d, %Y") + " - " + record.slip_id.date_from.strftime("%B %d, %Y")
  
    def _compute_over_contract_name(self):
        for record in self:
            record.over_contract_name = record.slip_id.contract_id.name



    

    