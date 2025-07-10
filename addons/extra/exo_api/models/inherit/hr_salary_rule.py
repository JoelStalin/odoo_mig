from odoo.exceptions import ValidationError
from odoo import models, fields, http, _

class hr_salary_rule_inherit(models.Model):
    _inherit = "hr.salary.rule"

    _excel_rule_name = fields.Char("Nombre a mostrar en el excel", required=True)

    send_to_email_or_download = fields.Boolean(
        string="Permite Enviar al Email y/o Descargar",
        help="Indica si esta regla se puede enviar por email y/o descargar.")