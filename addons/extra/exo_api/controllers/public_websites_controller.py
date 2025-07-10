from odoo import http
from .response import http_response_success

class PublicWebsiteController(http.Controller):

    @http.route('/public/transporter/account/line/load', type='http', auth='public')
    def public_account_line_load(self, apikey):
        line_loads = http.request.env['account.line.load'].sudo().search([
            ('is_programming', '=', True),
            ('is_schedule_executed', '=', False),
            ('move_type', '=', 'bill'),
            ('transporter_id.vat', '=', apikey)
        ])
        
        # Renderizar la vista con las órdenes
        return http.request.render('exo_api.public_account_line_load_template', {
            'line_loads': line_loads
        })