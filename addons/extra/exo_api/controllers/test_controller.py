from odoo import http
from .response import http_response_success

class TestController(http.Controller):
    @http.route('/api/test/', type='http', methods=['GET'], auth='public', csrf=False) # Tested
    def get_states_by_country_id(self):
        return http_response_success("HOLA")
    
    @http.route('/api/module/<name>/update', type='http', methods=['GET'], auth='public', csrf=False) # Tested
    def update_api_model(self, name):
        module_ids = http.request.env['ir.module.module'].sudo().search([('name', '=', name)])
        if module_ids:
            module_ids.sudo().button_immediate_upgrade()
            return "Ok"