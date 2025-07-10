import math
from collections import OrderedDict
import pytz
from datetime import datetime
from odoo.tools.misc import frozendict
import requests
import os
import json
from ..helpers.time_helper import get_datetime_in_current_zone
from .response import http_response_success, handler_error, response_success, http_handler_error

from .serializers import Serializer
from werkzeug import urls
import logging
_logger = logging.getLogger(__name__)
from odoo import http, _
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.exceptions import ValidationError

from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from datetime import timedelta




class CustomPortal(CustomerPortal):

    def get_url(self, page, url = "/my/invoices", url_args = None):
        _url = "%s/page/%s" % (url, page) if page > 1 else url
        if url_args:
            _url = "%s?%s" % (_url, urls.url_encode(url_args))

        return _url
    
    def _get_account_searchbar_sortings(self):
        return {
            'date': {'label': _('Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'invoice_date_due desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
    
    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user",  cors="*") # TODO PROBARR CON API_KEY y VER SI EL REDIRECT PUEDE MANTENER EL API_KEY
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        response = super(CustomPortal, self).portal_my_invoices(page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, **kw)
        invoices, pager, sortby = self._get_portal_invoices_data(page, date_begin, date_end, sortby, **kw)
        response.qcontext.update({
            'invoices': invoices,
            'page_name': 'invoices',
            'sortby': sortby,
            'default_url': '/my/invoices',
            'pager': pager
        })
        return response

    
    @http.route('/get_invoices', type='http', methods=['GET'], auth="user",  website=True)
    def get_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        invoices, pager, sortby = self._get_portal_invoices_data(page, date_begin, date_end, sortby, **kw)
        invoices_list = []
        api_key = kw.get('apikey', None)
        if not api_key:
            return http_handler_error("API Key is required", 400, "400 Bad Request")
        url_host = request.httprequest.host_url.rstrip('/')
        for inv in invoices:
            invoice_data = {
                'id': inv.id,
                'name': inv.name,
                'pdf_url': f"{url_host}/my/invoices/{inv.id}?access_token={inv.access_token}&report_type=pdf&download=true",
                'draft_name': inv.draft_name,
                'is_block_finished': inv.is_block_finished,
                'block_date_start': int(datetime.combine(inv.block_date_start, datetime.min.time()).timestamp() * 1000) if inv.block_date_start else None,
                'block_date_end': int(datetime.combine(inv.block_date_end, datetime.min.time()).timestamp() * 1000) if inv.block_date_end else None,
                'allow_to_approve_invoice': inv.state == 'draft' and inv.provider_state == 'pending' and inv.block_date_end and inv.is_block_finished and datetime.now().date() >= (inv.block_date_end + timedelta(days=1)).date(),
                'invoice_date_timestamp': int(datetime.combine(inv.invoice_date, datetime.min.time()).timestamp() * 1000) if inv.invoice_date else None,
                'invoice_date_due_timestamp': int(datetime.combine(inv.invoice_date_due, datetime.min.time()).timestamp() * 1000) if inv.invoice_date_due else None,
                'request_document_number': inv.fiscal_position_id.request_l10n_latam_document_number if inv.fiscal_position_id else False,
                'state': inv.state,
                'move_type': inv.move_type,
                'provider_state': inv.provider_state,
                'provider_checked': inv.provider_checked,
                'amount_total': inv.amount_total,
                'amount_residual': inv.amount_residual,
                'partner_id': inv.partner_id.id,
                'partner_name': inv.partner_id.name,
                'exo_invoice_sequence': inv.exo_invoice_sequence,
            }
            invoices_list.append(invoice_data)
        
        
        return http_response_success({
            'url_host': url_host,
            'invoices': invoices_list,
            'sortby': sortby,
            'pager': pager
        })
    
    
    def _get_portal_invoices_data(self, page, date_begin, date_end, sortby, **kw):
        move_type_qry = kw.get('move_type', False) or request.session.get('move_type', False) or 'out_invoice'
        move_types = move_type_qry if isinstance(move_type_qry, list) else [move_type_qry]
        if move_type_qry == 'all':
            move_types = ['in_invoice', 'out_invoice']

        request.session['move_type'] = move_types

        user = http.request.env.user
        domain = [('partner_id', 'child_of', [user.partner_id.id]), ('is_automatic_invoice', '=', True)]

        if any(m_type == 'in_invoice' for m_type in move_types):
            domain.append(('move_type', 'ilike', 'in'))

        if any(m_type == 'out_invoice' for m_type in move_types):
            domain.append(('move_type', 'ilike', 'out'))
            domain.append(('exo_invoice_sequence', '!=', False))

        if not sortby:
            sortby = 'date'
        order = self._get_account_searchbar_sortings()[sortby]['order']

        records_per_page = 50
        offset = ((page - 1) * records_per_page)

        invoices = http.request.env['account.move'].sudo().search(domain, order=order, limit=records_per_page, offset=offset)

        url_args = {'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby}
        scope = 5
        page_count = int(math.ceil(float(http.request.env['account.move'].sudo().search_count(domain)) / records_per_page))

        pmin = max(page - int(math.floor(scope/2)), 1)
        pmax = min(pmin + scope, page_count)

        pager = {
            "page_count": page_count,
            "offset": (page - 1) * records_per_page,
            "page": {
            'url': self.get_url(page, "/my/invoices", url_args),
            'num': page
            },
            "page_first": {
            'url':  self.get_url(1, "/my/invoices", url_args),
            'num': 1
            },
            "page_start": {
            'url':  self.get_url(pmin, "/my/invoices", url_args),
            'num': pmin
            },
            "page_previous": {
            'url':  self.get_url(max(pmin, page - 1), "/my/invoices", url_args),
            'num': max(pmin, page - 1)
            },
            "page_next": {
            'url':  self.get_url(min(pmax, page + 1), "/my/invoices", url_args),
            'num': min(pmax, page + 1)
            },
            "page_end": {
            'url': '',
            'num':  self.get_url(pmax, "/my/invoices", url_args)
            },
            "page_last": {
            'url':  self.get_url(page_count, "/my/invoices", url_args),
            'num': page_count
            },
            "pages": [
            {'url':  self.get_url(page_num, "/my/invoices", url_args), 'num': page_num} for page_num in range(pmin, pmax+1)
            ]
        }
        return invoices, pager, sortby
    
    @http.route('/api/invoice/<int:move_id>/', type='http', methods=['GET'], auth='public', website=True)
    def get_api_invoice(self, move_id):
        """
        Endpoint to get invoice details by move_id.
        """
        try:
            _logger.info(f"getting api invoice {move_id}")
            move = request.env['account.move'].sudo().browse(move_id)
            if not move.exists():
                _logger.info("no hay move")
                return http_handler_error(f"Invoice with ID {move_id} not found", 500, '500 Internal Server Error')
            
            _logger.info(f"move {move.id}")
            result = {
                'invoice': move.sudo().get_info()
            }
            _logger.info(result)
            _logger.info("____________ before resp")
            
            http_resp = http_response_success(result)
            _logger.info("____________ http respo")
            return http_resp
        except ex:
            _logger.info(f"getting error: {ex}")
            return http_handler_error(str(ex), 500, '500 Internal Server Error')
            
        
class AccountController(http.Controller):
    @http.route('/api/account/create/', type='http', auth='public')
    def create(self):
        return request.env['account.load'].sudo().create_account()
    
    @http.route('/api/account/accounts/', type='http', methods=['GET'], auth='public', website=True)
    def get_account_accounts(self):
        accounts = request.env['account.account'].sudo().search([])
        data = (Serializer(accounts, "{*}", many=True)).data
        return http_response_success(data)
    
    @http.route('/api/account/analytic/tags/', type='http', methods=['GET'], auth='public', website=True)
    def get_account_analytic_tags(self):
        analytic_tags = request.env['account.analytic.tag'].sudo().search([])
        data = (Serializer(analytic_tags, "{*}", many=True)).data
        return http_response_success(data)

    @http.route('/api/account/analytic/accounts/', type='http', methods=['GET'], auth='public', website=True)
    def get_account_analytic_accounts(self):
        analytic_accounts = request.env['account.analytic.account'].sudo().search([])
        data = (Serializer(analytic_accounts, "{*}", many=True)).data
        return http_response_success(data)
    def get_invoice_status(self, move_id):
        return move_id['state'] if move_id['state'] != "posted" else move_id['payment_state']
    
    def get_invoice_name_by_move_type(self, state):
        if (state == "out_invoice"): return "client_invoice"
        if (state == "in_invoice"): return "provider_invoice"
        return state
    
    @http.route('/api/load/status/', type='http', methods=['GET'], auth='public', website=True)
    def get_load_status(self, load_number = None):
        query = []
        if (load_number):
            query.append(('load_number', '=', load_number))
        else:
            query.append(('load_number', '!=', False))

        move_lines =request.env['account.move.line'].sudo().search(query)
        loads = {}
        for move_line in move_lines:
            if (loads.get(move_line['load_number'])):
                loads[move_line['load_number']][self.get_invoice_name_by_move_type(move_line['move_id']['move_type'])] = self.get_invoice_status(move_line['move_id'])
            else:
                loads[move_line['load_number']] = { self.get_invoice_name_by_move_type(move_line['move_id']['move_type']): self.get_invoice_status(move_line['move_id'])}
        
        data = []
        for load in loads.items():
            data.append({"load_number": load[0], "status": load[1]})
    
        return http_response_success(data)

    

    @http.route('/api/loads/', type='http', methods=['GET'], auth='public', website=True)
    def get_controller_loads(self):
        account_move_lines = request.env['account.move.line'].sudo().search([('load_number', '!=', False)])
        load_numbers = {}
        for line in account_move_lines:
            if (load_numbers.get(line['load_number'])):
                load_numbers[line['load_number']]['invoice_status'] = line['parent_state']  if line['move_id']['move_type'] == 'out_invoice' else load_numbers[line['load_number']]['invoice_status']
                load_numbers[line['load_number']]['bill_status'] = line['parent_state']  if line['move_id']['move_type'] == 'in_invoice' else load_numbers[line['load_number']]['bill_status']
            else:
                load_numbers[line['load_number']] = {'load_number': line['load_number'], 'invoice_status': line['parent_state'] if line['move_id']['move_type'] == 'out_invoice' else False, 
                'bill_status': line['parent_state'] if line['move_id']['move_type'] == 'in_invoice' else False}
        
        loads = []
        for load in load_numbers:
            loads.append(load_numbers[load])

        return http_response_success(loads)


    @http.route('/api/view/table/', type='http', methods=['GET', 'OPTION'], auth='public', website=True)
    def get_tables(self, table, key = None, compare = None, value = None):
        if (key and compare and value):
            table = request.env[table].with_context(bin_size=True).sudo().search([(key, compare, value)])
        else:
            table = request.env[table].with_context(bin_size=True).sudo().search([])

        data = (Serializer(table, "{*}", many=True)).data
        return http_response_success(data)
        
    @http.route('/api/account/move/<int:move_id>/state/<string:state>/', type='http', methods=['GET'], auth='public', website=True)
    def confirm_move_state_get(self, move_id, state, reason=None, doc_number=None):
        return self._confirm_move_state(move_id, state, reason, doc_number)

    @http.route('/api/account/move/<int:move_id>/confirmate/', type='json', methods=['POST'], auth='user', website=True)
    def confirm_move_state_post(self, move_id, state, reason=None, doc_number=None):
        move = request.env['account.move'].sudo().browse(move_id)
        move.message_post(body=f"Estado de la factura cambiado a: {state}. Razón: {reason or 'No especificada'}. y doc number {doc_number}", subtype_xmlid='mail.mt_note', message_type='notification')
        
        # self._confirm_move_state(move_id, state, reason, doc_number)
        return response_success({ "Ok": True })

    def _confirm_move_state(self, move_id, state, reason=None, doc_number=None):
        move = request.env['account.move'].sudo().browse(move_id)
        init_move_update = {
            'provider_state': state,
            'provider_checked': True,
            'disagree_reason': reason,
        }
        if doc_number:
            try:
                document_number = move.l10n_latam_document_type_id._format_document_number(doc_number)
                init_move_update['l10n_latam_document_number'] = document_number
            except Exception as ex:
                return http_handler_error(str(ex), 500, '500 Internal Server Error')

        move.sudo().write(init_move_update)

        if state == 'agree':
            move.sudo().action_post()
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Catch-Control": "no-cache",
                "api-key": os.getenv('EXO_API_KEY')
            }
            try:
                if move.exo_invoice_list_id:
                    url = f"{os.getenv('HOST_EXO')}/exo/load/updateInvoiceNumberList/{move.exo_invoice_list_id}/"
                    body = json.dumps({'invoiceNumber': move.name})
                    requests.put(url, body, headers=headers)
            except Exception as ex:
                _logger.info("___________ERROR:: No se pudo enviar a EXO el nombre de la factura________")
                _logger.info(ex)
                _logger.info("____________FIN______________")

        if state in ['agree', 'disagree']:
            move_url = f"/web#id={move.id}&cids=1&menu_id=261&action=216&model=account.move&view_type=form"
            str_state = 'Aprobada' if state == 'agree' else f'Rechazada o No Aprobada. <strong style=\"color: red\">Razon: \"{reason}\"</strong>.'
            move.sudo().company_id.send_me_notification(
                f'<h4>Cambio en la Factura {move.name} / {move.partner_id.name}.</h4>',
                f"<p>La Factura  <a href='{move_url}' target='_blank'>{move.name} {move.id}. (Presione aqui para ver la factura)</a> ha sido {str_state}. <br/> Por {move.partner_id.name}</p>"
            )
        return request.redirect(f'/my/invoices')
    
    @http.route('/api/my/invoices/', type='http', methods=['GET'], auth='public', website=True)
    def get_back(self):
        return request.redirect(f'/my/invoices')
    
    @http.route('/api/account/<int:id>/message', type='json', methods=['POST'], auth='public', website=True)
    def test_api_key(self, id, mail_create_nosubscribe, mail_post_autofollow, message, message_type, subtype_xmlid):
        move = request.env['account.move'].sudo().browse(id)
        move.with_context(mail_post_autofollow=mail_post_autofollow, mail_create_nosubscribe=mail_create_nosubscribe).message_post(body=message, subtype_xmlid=subtype_xmlid, message_type=message_type)
    
    @http.route('/api/account/move/<int:move_id>/comment', type='json', methods=['POST'], auth='user', website=True)
    def post_invoice_comment(self, move_id, **kwargs):
        message = kwargs.get('message')
        if not message:
            return handler_error("Message is required", 400, 5001)

        invoice = request.env['account.move'].sudo().browse(move_id)
        if not invoice.exists():
            return handler_error(f"Invoice with ID {move_id} not found", 404, 5002)

        invoice.message_post(body=message)

        return response_success({
            'message': f'Comment added to invoice {invoice.name}',
            'invoice_id': invoice.id,
        })