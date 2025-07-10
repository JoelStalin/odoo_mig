from odoo import http, fields
from .response import http_response_success, handler_error, response_success, http_handler_error
import logging
import datetime
import time
import requests
import json
import os
import string

from ..helpers.request_helper import get_cookie

import logging
_logger = logging.getLogger(__name__)


def json_response(body, status = 200):
    return {'body': body, 'status': status}

class LoadController(http.Controller):
    @http.route(['/api/load/<load_id>/statuses/'], type='http', auth="public", methods=['GET'],  csrf=False) # Tested
    def get_loadmaps_statuses_by_id(self, load_id, language = 'en'):
        try:
            load = http.request.env['account.line.load'].sudo().search([('load_id', '=', load_id)])
            groups_statuses = load.sudo().getLoadStatuses(language)
            statuses = groups_statuses[0]['statuses'] if len(groups_statuses) > 0 else []
        except Exception as ex:
            _logger.info(ex)
            return http_handler_error("No se ha podido generar los statuses", 500, '500 Internal Server Error')

        return http_response_success({
            "statuses": statuses
        })
    
    @http.route(['/api/loads/updated/'], type='http', auth="public", methods=['GET'], csrf=False)
    def get_loads_by_update_date(self, start_timestamp=None, end_timestamp=None, page=None, limit=None):
        domain = []
        if start_timestamp:
            start_timestamp = float(start_timestamp) / 1000 if len(str(start_timestamp)) > 11 else float(start_timestamp)
            start_date = datetime.datetime.fromtimestamp(start_timestamp)
            domain.append(('write_date', '>=', start_date))
        if end_timestamp:
            end_timestamp = float(end_timestamp) / 1000 if len(str(end_timestamp)) > 11 else float(end_timestamp)
            end_date = datetime.datetime.fromtimestamp(end_timestamp)
            domain.append(('write_date', '<=', end_date))

        result = self._get_loads_with_pagination(domain, page, limit)
        
        return http_response_success({
            'count': len(result.get('loads', [])),
            "loads": result.get('loads', []),
            "total_count": result.get('total_count', 0),
            "page": page,
            "limit": limit
        })

    def _get_loads_with_pagination(self, domain, page=None, limit=None):
        total_count = http.request.env['account.line.load'].sudo().search_count(domain)
        if page is not None and limit is not None:
            page = int(page)
            limit = int(limit)
            offset = (page - 1) * limit
            loads = http.request.env['account.line.load'].sudo().search(domain, offset=offset, limit=limit)
        else:
            # Sin paginación, traer todos los registros
            loads = http.request.env['account.line.load'].sudo().search(domain)
        
        return {
            'total_count': total_count,
            'loads': loads.getLoadStatuses()
        }
        
        

    @http.route(['/api/loads/statuses/'], type='http', auth="public", methods=['GET'],  csrf=False) # Tested
    def get_all_loads_by_date(self, load_ids = None, start_date_tstamp = None, end_date_tstamp = None, page=None, limit=None):
        domain = []
        if (start_date_tstamp and end_date_tstamp):
            start_date_tstamp = float(start_date_tstamp) / 1000 if len(str(start_date_tstamp)) > 11 else float(start_date_tstamp)
            end_date_tstamp = float(end_date_tstamp) / 1000 if len(str(end_date_tstamp)) > 11 else float(end_date_tstamp)
                
                
            start_date = datetime.datetime.fromtimestamp(start_date_tstamp)
            end_date = datetime.datetime.fromtimestamp(end_date_tstamp)
            
            domain.append(('create_date', '>=', start_date))
            domain.append(('create_date', '<', end_date))
        
        if (load_ids):
            load_ids_array = load_ids.split(',')
            
            domain = []
            index = 0
            for load_id in load_ids_array: 
                domain = ['|'] + domain if index > 0  else domain
                domain = domain + [('original_load_id', 'ilike', load_id)] # ['|', ('load_id', 'ilike', 'load_1')]
                index += 1

        _logger.info("__________________ domain ||||||")
        _logger.info(domain)
        # Si los parámetros de paginación están presentes, aplicarlos
        result = self._get_loads_with_pagination(domain, page, limit)
        return http_response_success({
            'count': len(result.get('loads', [])),
            "loads": result.get('loads', []),
            "total_count": result.get('total_count', 0),
            "page": page,
            "limit": limit
        })
    
    
    @http.route(['/api/invoice/rnc/<rnc>'], type='json', auth="public", methods=['POST'],  csrf=False) # Tested
    def create_draft_from_loads(self, rnc, exo_invoice_list_id, sequence_number, load_ids):
        
        if (not load_ids or len(load_ids) == 0):
            return http_handler_error("No se ha recibido loads", 400, '400 Bad Request')

        try:
            cookie = get_cookie()
            document_number = http.request.env['account.load'].sudo().transform_rnc(rnc)
            
            partner = http.request.env['res.partner'].sudo().search([('vat', '=', document_number)], limit=1)
            if (not partner):
                return json_response("Cliente no encontrado", 404)
                
            created_record = http.request.env['account.load'].sudo().create({
                'start_date': fields.Datetime.now(),
                'end_date': fields.Datetime.now(),
                'account_load_client_id': partner.id,
                'has_error_continue_others': False
            })
            group_request_code = str(int(time.time() * 100))
            searched_record = http.request.env['account.load'].sudo().browse(created_record.id)
            batch_size = 20
            invoices = []
            r = range(0, len(load_ids), batch_size)
            for i in r:
                load_batched = load_ids[i: i + batch_size]
                invoices += searched_record.execute_load(cookie, None, True,  False, http.request.env, load_batched, True, group_request_code)
                http.request.env.cr.commit()
                
            index = 0
            sufix = ''
            load_invoices = http.request.env['account.line.load'].sudo().search(['|', ('load_id', 'in', load_ids), ('original_load_id', 'in', load_ids)])
            line_moves = load_invoices.mapped('account_move_id')
            for invo in line_moves:
                if (index == 25):
                    index = 0
                    sufix = "-" + str(1 if not sufix else sufix + 1)
                    
                letter = string.ascii_uppercase[index]
                invo.sudo().write({
                    'exo_invoice_list_id': exo_invoice_list_id if exo_invoice_list_id else 'NO EXO INVOICE LIST ID',
                    'exo_invoice_sequence': f"{sequence_number}-{letter}{sufix}",
                    'lock_invoice': True
                })
                    
                index += 1
            
            
            moves = []
            
            for inv in invoices:
                moves.append(inv)
                
            for linv in line_moves:
                moves.append(linv)
            
            all_invoices = list(set(moves))
            
            return json_response(self.get_line_load_data(all_invoices, load_ids))
            
        except Exception as e:
            _logger.info("_+_________________________________ERRROOOOOOOOOOOOOOOOOOR__________________________")
            _logger.info(e)
            return json_response(str(e), 500)
            
    
    def get_line_load_data(self, current_invoices, load_ids):
        move_ids = [inv.id for inv in current_invoices]
        line_loads = http.request.env['account.line.load'].sudo().search([('account_move_id', 'in', move_ids)])
        create_load_ids = [line_load.original_load_id or line_load.load_id for line_load in line_loads]
        
        # Resultado inicial
        result = {
            'invoices': [invoice['id'] for invoice in current_invoices],
            'in_accounting': [{'load_id': line.original_load_id or line.load_id, 'move': {'id': line.account_move_id.id, 'name': line.account_move_id.name}} for line in line_loads],
            'not_in_accounting': [{'load_id': load, 'move': False} for load in load_ids if load not in create_load_ids],
        }

        # Filtrar elementos duplicados
        def remove_duplicates(items, key_func=lambda x: x):
            seen = set()
            unique_items = []
            for item in items:
                key = key_func(item)
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
            return unique_items

        result['invoices'] = list(set(result['invoices']))  # Filtrar ids únicos
        result['in_accounting'] = remove_duplicates(result['in_accounting'], key_func=lambda x: x['load_id'])  # Filtrar por 'load_id'
        result['not_in_accounting'] = remove_duplicates(result['not_in_accounting'], key_func=lambda x: x['load_id'])  # Filtrar por 'load_id'

        self.send_load_in_accounting(line_loads)
        return result
    
    def send_load_in_accounting(self, lines):
        data = { "email": str(os.getenv('EXO_USER')), "password": str(os.getenv('EXO_PASSWORD'))}
        endpoint_url = str(os.getenv('HOST_EXO')) + '/exo/authenticate/'

        responseAuthenticate = requests.post(url=endpoint_url, json=data)

        if responseAuthenticate.status_code != 200:
            raise ValidationError('La carga no pudo ser procesada debido a temas de authenticacion con EXO. \nCode: %s\nContent: %s' % (responseAuthenticate.status_code, responseAuthenticate.content))
        
        resp  = responseAuthenticate.json()
        cookie = resp['data']['cookie'][0]
        
        lines.update_in_accounting_loads(cookie)
