from odoo.exceptions import ValidationError
from odoo import models, fields, http, _, api
from odoo.tools.misc import xlsxwriter
import base64
import io

import logging
_logger = logging.getLogger(__name__)
class hr_payslip_inherit(models.Model):
    _inherit = "hr.payslip"


    download_line_ids = fields.One2many(
        'hr.payslip.line', 'slip_id', string='Payslip Download Lines',
        compute='_compute_download_line_ids')

    def _compute_download_line_ids(self):
        for payslip in self:
            payslip.download_line_ids = payslip.line_ids.filtered(lambda p: p.salary_rule_id.send_to_email_or_download == True )

    def send_salary_computation_by_email(self):
        hr_payslip_templates = http.request.env['mail.template'].sudo().search([('model', '=', 'hr.payslip')])
        default_template = False
        if (len(hr_payslip_templates) > 0):
            default_template = hr_payslip_templates[0]
        
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='hr.payslip',
            default_res_id=self.id,
            default_use_template=bool(default_template),
            default_template_id=default_template and default_template.id,
            default_composition_mode='comment',
            custom_layout='exo_api.mail_hr_payslip_salary',
            mark_coupon_as_sent=True,
            force_email=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }