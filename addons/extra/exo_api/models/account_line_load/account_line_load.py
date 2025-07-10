from urllib.parse import quote
import uuid
import collections.abc
from datetime import date, timedelta, datetime, timedelta
import pytz
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
import json
import os
from ...helpers.load_helper import get_orders_in_ids
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

PAYMENT_STATE_SELECTION = {
    "es": {
        'not_paid': 'No Pagado',
        'in_payment': 'En Proceso de Pago',
        'paid': 'Pagado',
        'partial': 'Particialmente pagado',
        'reversed': 'Factura Reversada',
        'invoicing_legacy': 'Factura del viejo odoo',
    },
    "en": {
        'not_paid': 'Unpaid',
        'in_payment': 'In Payment Process',
        'paid': 'Paid',
        'partial': 'Partially paid',
        'reversed': 'Reversed Invoice',
        'invoicing_legacy': 'Invoicing Legacy',
    }
}

MESSAGE_LANGUAGE_SELECTION = {
    "en": {
        "received_in_accounting": "Received in Accounting",
        "invoiced_shipper": "Invoiced to Shipper",
        "invoice_of_shipper": "Shipper's Invoice",
        "billed_transporter": "Billed to Transporter",
        "bill_transporter": "Transporter's Bill",
        "without_payment_status": "(Without payment status)",
        "in_shipper_draft_invoice": "In shipper draft invoice",
        "in_transporter_draft_invoice": "In transporter draft invoice",
        "in_shipper_approved_invoice": "In shipper approved invoice",
        "in_transporter_approved_invoice": "In transporter approved invoice",
        "paid_by_shipper": "Paid by shipper",
        "paid_to_transporter": "Paid to transporter"
    },
    "es": {
        "received_in_accounting": "Recibido en Contabilidad",
        "invoiced_shipper": "Facturado al Shipper",
        "invoice_of_shipper": "Factura del Shipper ",
        "billed_transporter": "Facturado al Transportista",
        "bill_transporter": "Factura del Transportista ",
        "without_payment_status": "(Sin estado de pago)",
        
        "in_shipper_draft_invoice": "Borrador en el Shipper",
        "in_transporter_draft_invoice": "Borrador en el Transportista",
        "in_shipper_approved_invoice": "Facturada es aprobada en shipper",
        "in_transporter_approved_invoice": "Factura es aprobada en transportista",
        "paid_by_shipper": "Pagada por el shipper",
        "paid_to_transporter": "Pagada al transportista"
    },
}

class account_line_load_state(models.Model):
    _name = "account.line.load.state"
    _description = 'Estado de una linea de carga'
    
    name = fields.Char("Estado")
    
    
class account_line_load(models.Model):
    _name = "account.line.load"
    _description = 'EXO Load'

    name = fields.Char("Nombre", compute="_compute_name", store=True, readonly=True)
    driver = fields.Char('Conductor')
    status = fields.Char('Status')
    shipper = fields.Char('Shipper')
    load_id = fields.Char('Id de la Carga')
    original_load_id = fields.Char('Id de la Carga sin modificacion', store=True, compute='_compute_load_id')
    load_number = fields.Char('Numero de Carga')
    orders = fields.Char('Ordenes')
    json_current_load = fields.Text('Json de la carga con el cual se creó este registro', default= '{}')
    process_code_uuid = fields.Char('UUID')
    account_line_id = fields.Many2one('account.move.line', 'Linea de Factura', required=False, ondelete='cascade')
    account_move_id = fields.Many2one('account.move', 'Factura', store=True, compute='_compute_invoice')
    is_exo_refreshed = fields.Boolean('Esta actualizado con exo', default=False)
    move_type = fields.Selection([('invoice', 'Factura de un Shipper'), ('bill', 'Factura de un Transportista')], help="Indica si la carga se creo a partir de un factura de un cliente o de una factura de un tranportista")
    was_restored = fields.Boolean('Fue restaurada', default=False)
    
    
    quantity = fields.Float('Cantidad Solicitada')
    billPrice = fields.Float('Costo de Transportista')
    product_tmpl_id = fields.Many2one('product.template', 'Producto')
    is_programming = fields.Boolean('Es una carga programada', default=False)
    is_schedule_executed = fields.Boolean('La carga programada fue ejecutada', default=False)
    block_date_start = fields.Datetime(string='Fecha Inicio del Bloque')
    block_date_end = fields.Datetime(string='Fecha Fin del Bloque')
    transporter_id = fields.Many2one('res.partner', 'Odoo Transportista', relation='transporter_relation_id')
    shipper_id = fields.Many2one('res.partner', 'Odoo Shipper', relation='shipper_relation_id')
    is_exo_app = fields.Boolean('Fue creado desde una app de exo', default=False)
    group_code = fields.Boolean('Codigo de Agrupacion', default=False)
    load_date = fields.Datetime(string='Fecha de la factura en EXO')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    analytic_tag_ids = fields.Many2many(comodel_name='account.analytic.tag', string='Analytic Tag')
    account_line_load_state = fields.Many2one('account.line.load.state', 'Estado de una Linea de Carga')
    invoice_line_name = fields.Char('Factura + Carga', store=True, compute='_compute_invoice_plus_line')
    test_emy = fields.Boolean("Prueba")
    
    
    def create_in_invoice(self, current_env = None):
        current_env = current_env if current_env else request.env
        invoices_createds = []
        clients = {}
        for line in self.filtered(lambda l: not l.account_line_id):
            load = json.loads(line.json_current_load)
            current_transporter_partner = line['transporter_id']
            client_partner = line['shipper_id']
            product = line['product_tmpl_id']
            load_number_display = line['load_number'] 
           
            transporter_analytics_accounts = line['analytic_account_id']
            transporter_analytics_tags = line['analytic_tag_ids']
            
            taxes = product['taxes_id'] if product['taxes_id'] else []
            additional_taxes = current_transporter_partner.tax_products.filtered(lambda x: x.product_tmpl_id.id == product['id']) if current_transporter_partner.tax_products else []
            
            additional_tax_ids = [add_tax.tax_id.id for add_tax in additional_taxes]
            tax_ids = taxes.ids + additional_tax_ids
            current_transporter_partner.add_additional_tax(current_env, tax_ids)
            
            if (client_partner['in_transporter_show_order_num']):
                load_number_display = f"GUIA NO: ({str(line['orders'])}) / " + load_number_display
          
            domain = [('is_automatic_invoice', '=', True), ('lock_invoice', '=', False), ('partner_id', '=', current_transporter_partner['id']), ('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']), ('state', '=', 'draft')]

            group_key = line.group_code if line.group_code else ''
            if (line.is_exo_app):
                group_key += 'is_exo_app'
            
            if (group_key):
                domain.append(('load_invoice_code', '=', group_key))
            
            exists_invoice_from_partner = current_env['account.move'].sudo().search(domain)
            if (exists_invoice_from_partner == False or len(exists_invoice_from_partner) == 0):
                invoices_createds.append(exists_invoice_from_partner)
                
                invoice_line = (0, 0, {
                    'product_id': product.id,
                    'quantity': line['quantity'],
                    'name': load_number_display, 
                    'discount': False,
                    'price_unit': line['billPrice'],
                    'debit': line['billPrice'],
                    'credit': 0.0,
                    'account_id': product.property_account_expense_id.id,
                    'analytic_account_id': transporter_analytics_accounts,
                    'analytic_tag_ids': transporter_analytics_tags,
                    'tax_ids': tax_ids if len(tax_ids) > 0 else False,
                    'is_automatic_line': True,
                    'load_ids': [(4, line.id)]
                })
                
                client_key_group = str(current_transporter_partner['id']) + str(group_key)
                if (not clients.get(client_key_group)):
                    clients[client_key_group] = {"partner": current_transporter_partner,  "block": {'block_start': line.block_date_start, 'block_end': line.block_date_end }, 'load_invoice_code': group_key, "invoice_line_ids": []}
                
                clients[client_key_group]["invoice_line_ids"].append(invoice_line)
                
                for disc in load['transportationCostDiscount']:
                    dic_tax_ids = product.taxes_id.ids + []
                    current_transporter_partner.add_additional_tax(current_env, dic_tax_ids)
                    
                    clients[client_key_group]["invoice_line_ids"].append((0, 0, {
                        'product_id': product.id,
                        'quantity': disc['quantity'],
                        'name':  f"{load_number_display} / {disc['description']}", 
                        'discount': False,
                        'price_unit': disc['damagedChargePrice'] * (-1 if disc['type'] == "$ Descuento" else 1),
                        'analytic_account_id': transporter_analytics_accounts,
                        'analytic_tag_ids': transporter_analytics_tags,
                        'tax_ids': dic_tax_ids,
                        'load_ids': False,
                        'is_automatic_line': True,
                        'line_type': disc['type'],
                        'debit': 0 if disc['type'] == "$ Descuento" else disc['damagedChargePrice'],
                        'credit': disc['damagedChargePrice'] if disc['type'] == "$ Descuento" else 0,
                        'account_id': product.property_account_expense_id.id,
                    }))
                    
                    
            else:
                exists_invoice_from_partner.create_move_line_benefit_discount(current_env)
                move = exists_invoice_from_partner[0]
                move.sudo().write({
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'quantity': line['quantity'],
                        'name': load_number_display, 
                        'discount': False,
                        'price_unit': line['billPrice'],
                        'analytic_account_id': transporter_analytics_accounts.id,
                        'analytic_tag_ids': [(6, 0, transporter_analytics_tags.ids)],
                        'tax_ids': tax_ids if len(tax_ids) > 0 else False,
                        'move_id': move.id,
                        'debit': line['billPrice'],
                        'credit': 0.0,
                        'account_id': product.property_account_expense_id.id,
                        'is_automatic_line': True,
                        'load_ids': [(4, line.id)]
                    })]
                })
                invoices_createds.append(move)


        for client in clients:
            current_transporter_partner = clients[client]['partner']
            current_block = clients[client]['block']
            current_load_invoice_code = clients[client]['load_invoice_code']
            invoice = current_env['account.move'].sudo().create({
                'fiscal_position_id': current_transporter_partner.property_account_position_id.id,
                'invoice_payment_term_id': current_transporter_partner['property_supplier_payment_term_id'] if current_transporter_partner['property_supplier_payment_term_id'] else current_env.ref('account.account_payment_term_30days').id,
                'move_type': 'in_invoice',
                'partner_id': current_transporter_partner['id'],
                'invoice_date': date.today(),
                'invoice_line_ids': clients[client]['invoice_line_ids'],
                'is_automatic_invoice': True,
                'load_invoice_date': line['load_date'],
                'company_id': current_env.company.id,
                'load_invoice_code': current_load_invoice_code if current_load_invoice_code else False,
                'block_date_start': current_block['block_start'] if current_block else False,
                'block_date_end': current_block['block_end'] if current_block else False,
            })
            invoice.create_move_line_benefit_discount(current_env)
            if (invoice not in invoices_createds):
                invoices_createds.append(invoice)
                
        self.sudo().write({'is_schedule_executed': True})
    
    @api.depends('load_id', 'test_emy')
    def _compute_load_id(self):
        for record in self:
            record.original_load_id = record.load_id.split("_")[0] if record.load_id and len(record.load_id) > 0 else record.load_id
            
    @api.depends('account_move_id', 'account_move_id.name', 'load_number')
    def _compute_invoice_plus_line(self):
        for record in self:
            record.invoice_line_name = f"{record.account_move_id.id} / {record.account_move_id.name} / {record.load_number}"
        

    @api.depends('account_line_id', 'load_number')
    def _compute_name(self):
        for record in self:
            record.name = str(record.load_number) + '__' + str(record.account_line_id)
            

    def get_exo_cookie(self):
        data = { "email": str(os.getenv('EXO_USER')), "password": str(os.getenv('EXO_PASSWORD'))}
        endpoint_url = str(os.getenv('HOST_EXO')) + '/exo/authenticate/'
        responseAuthenticate = requests.post(url=endpoint_url, json=data)
        if responseAuthenticate.status_code != 200:
            raise ValidationError('La carga no pudo ser procesada debido a temas de authenticacion. \nCode: %s\nContent: %s' % (responseAuthenticate.status_code, responseAuthenticate.content))
        
        resp  = responseAuthenticate.json()
        cookie = resp['data']['cookie'][0]
        return cookie
    
    def chunk_records(self, chunk_size):
        """Divide una lista en trozos de tamaño chunk_size."""
        for i in range(0, len(self), chunk_size):
            yield self[i:i + chunk_size]
        
    def refresh_loads_with_exo(self):
        cookie = self.get_exo_cookie()
        for record_chunk in self.chunk_records(50):
            exo_json_data = record_chunk.get_exo_loads(cookie)
            if (exo_json_data and len(exo_json_data) > 0):
                for record in record_chunk:
                    json_value = next(filter(lambda item:  item["loadNumber"].lower() == record.load_number.lower(), exo_json_data), None)
                    if (json_value):
                        record.sudo().write({
                            'driver': json_value.get('driver', False),
                            'status': json_value.get('status', False),
                            'shipper': json_value.get('shipper', False),
                            'load_id': json_value.get('loadId', False),
                            'orders': get_orders_in_ids(json_value.get('orders', [])),
                            'json_current_load': json.dumps(json_value),
                            'process_code_uuid': str(uuid.uuid4()),
                            'is_exo_refreshed': True
                        })
                    
            
    def get_exo_loads(self, cookie):
        load_numbers = [record.load_number for record in self]
        
        query = { 'loadNumber': load_numbers }
        host_exo = os.getenv('HOST_EXO')
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "auth": cookie 
        }
        
        url = f'{host_exo}/exo/loads/filterAll/'
        body = {
            'skip': 0,
            'take': 100,
            'query': query
        }
        response = requests.post(url, json.dumps(body) , headers=headers)
        result = response.json()
        
        if (not isinstance(result, dict) or
            not result.get("loads") or
            not result["loads"].get("Success")):
            raise ValidationError(f"Las cargas {query} no pudieron ser procesada. Favor comuníquese con su administrador e intente más tarde.")
        
        return result['loads']['Result']['data'] if len(result['loads']['Result']['data']) > 0 else []
            
        
    @api.depends('account_line_id.move_id')
    def _compute_invoice(self):
        for line_load in self:
            line_load.account_move_id = line_load.account_line_id.move_id
    
    def unlink(self):
        self.env['account.line.deleted.load'].create_deleted(self)
        self.sudo().update_status_in_exo('unlink')
        return super(account_line_load, self).unlink()

    def update_status_in_exo(self, type='update'):
        language = 'en'
        if (type == 'unlink'):
            statusesByLoad = []
            for record in self:
                statusesByLoad.append({
                    'load_id': record.load_id,
                    'original_load_id': record.original_load_id,
                    'statuses': [
                        {'name': 'rcv_accounting', 'date': datetime.now().timestamp(), 'description': MESSAGE_LANGUAGE_SELECTION[language]['received_in_accounting'], 'completed': False},
                        {'name': 'created_shipper_invoice', 'date': datetime.now().timestamp(), 'description': MESSAGE_LANGUAGE_SELECTION[language]['invoiced_shipper'], 'completed': False},
                        {'name': 'created_transporter_invoice', 'date': datetime.now().timestamp(), 'description': MESSAGE_LANGUAGE_SELECTION[language]['billed_transporter'], 'completed': False},
                        {'name': 'shipper_payment_state_invoice', 'date': datetime.now().timestamp(), 'description': f"{MESSAGE_LANGUAGE_SELECTION[language]['invoice_of_shipper']}" , 'completed': False},
                        {'name': 'transporter_payment_state_invoice', 'date': datetime.now().timestamp(), 'description': f"{MESSAGE_LANGUAGE_SELECTION[language]['bill_transporter']}", 'completed': False}
                    ]
                })
        else:
            statusesByLoad = self.sudo().getLoadStatuses(language)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Catch-Control": "no-cache",
            "api-key": os.getenv('EXO_API_KEY')
        }
        if ('contabilidadtest' not in os.getenv('HOST_EXO') ):
            url = f"{os.getenv('HOST_EXO')}/loads/allStatus/odoo"
            data = json.dumps(statusesByLoad)
            response = requests.put(url, data, headers=headers)
    
    
    def update_in_accounting_loads(self, cookie):
        load_ids = list(set([line['load_id'] for line in self]))
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Catch-Control": "no-cache",
            "auth": cookie,
        }
        if ('contabilidadtest' not in os.getenv('HOST_EXO') ):
            url = f"{os.getenv('HOST_EXO')}/exo/loads/allEvent"
            data = json.dumps({
                "event":"recieveInAccounting",
                "loadIds": load_ids,
                "user":"Odoo Acounting"
            })
            _logger.info("_______________ update_in_accounting_loads")
            _logger.info(data)
            response = requests.post(url, data, headers=headers)
            _logger.info("_______________ update_in_accounting_loads")
            _logger.info(response)
            if not response.ok:
                raise ValidationError(f"No se pudo actualizar el estado en EXO. Error: {str(response.content)}")
            
    def get_min_date(self, dates):
        return min(dates).timestamp() * 1000 if dates and len(dates) else None

    def get_self_load_in_groups(self):
        groups_by_load_id = {}
        groups_by_original_load_id = {}
        
        for record in self:
            
            if record.load_id in groups_by_load_id:
                groups_by_load_id[record.load_id].append(record)
            else:
                groups_by_load_id[record.load_id] = [record]
                
            if record.original_load_id in groups_by_original_load_id:
                groups_by_original_load_id[record.original_load_id].append(record)
            else:
                groups_by_original_load_id[record.original_load_id] = [record]
                
        return groups_by_load_id 
        # {'groups_by_load_id': groups_by_load_id, 'groups_by_original_load_id': groups_by_original_load_id} 
    
    def set_self_load_in_groups(self, groups):
        for load_id, records in groups.items():
            for sub_record in self:
                
                original_load_id = load_id.split("_")[0] if load_id and isinstance(load_id, str) and len(load_id) > 0 else load_id
                _logger.info(sub_record)
                
                move_type = sub_record['move_type'] == 'bill'
                is_sub_load = "_" in load_id if isinstance(load_id, str) else False
                is_same_load = original_load_id == sub_record['load_id']
                
                if ( move_type and is_sub_load and is_same_load):
                    groups[load_id].append(sub_record)
        
        
    def getLoadStatuses(self, language = 'en'):
        groups = self.get_self_load_in_groups()
        self.set_self_load_in_groups(groups)
        groups_statuses = []
        for load_id, records in groups.items():
            load_details = []
            for sub_record in records:
                obj = {
                    'load_id': sub_record['original_load_id'],
                    'sub_load_id': sub_record['load_id'],
                    'load_number': sub_record['load_number'],
                    'write_date': int(sub_record['write_date'].timestamp() * 1000) if sub_record['write_date'] else None,
                    'create_date': int(sub_record['create_date'].timestamp() * 1000) if sub_record['create_date'] else None,
                    'shipper': sub_record['shipper'],
                    'driver': sub_record['driver'],
                    'invoice_owner': sub_record['account_move_id']['partner_id']['name'] if 'account_move_id' in sub_record else None,
                    'invoice_type': 'transporter' if sub_record['move_type'] == 'bill' else 'shipper',
                    'account_line_subtotal': sub_record['account_line_id']['price_subtotal'] if 'account_line_id' in sub_record else None,
                    'invoice': {
                        'id': sub_record['account_move_id']['id'],
                        'total': sub_record['account_move_id']['amount_total_signed'],
                        'name': sub_record['account_move_id']['name']
                    } if 'account_move_id' in sub_record else None
                }
                load_details.append(obj)
            
            
            rcv_accounting_date = self.get_min_date([line_load['create_date'] for line_load in records])
            
            
            created_shipper_invoice_date = self.get_min_date([datetime.combine(line_load['account_move_id']['invoice_date'], datetime.min.time()) for line_load in records if line_load['move_type'] == 'invoice' and line_load["account_move_id"].state in ['posted']] )
            created_transporter_invoice_date = self.get_min_date([datetime.combine(line_load['account_move_id']['invoice_date'], datetime.min.time()) for line_load in records if line_load['move_type'] == 'bill' and line_load["account_move_id"].state in ['posted']])

            shipper_payment_state_invoice_date_list_dates =[line_load['create_date'] for line_load in records if line_load['move_type'] == 'invoice' and line_load["account_move_id"].payment_state in ['paid', 'reversed'] and line_load['account_move_id']['last_payment']  ]
            
            shipper_payment_state_invoice_date =  datetime.combine(min(shipper_payment_state_invoice_date_list_dates), datetime.min.time()).timestamp() if shipper_payment_state_invoice_date_list_dates else None
            
            transporter_payment_state_invoice_list_dates = [line_load['create_date'] for line_load in records if line_load['move_type'] == 'bill' and line_load["account_move_id"] and line_load["account_move_id"].payment_state in ['paid', 'reversed'] and line_load['account_move_id']['last_payment']  ]
            transporter_payment_state_invoice_date =  datetime.combine(min(transporter_payment_state_invoice_list_dates), datetime.min.time()).timestamp() if transporter_payment_state_invoice_list_dates else None
            
            shipper_payment_state_invoice_comments_list = [PAYMENT_STATE_SELECTION[language][line_load["account_move_id"].payment_state] for line_load in records if line_load["account_move_id"] and line_load['move_type'] == 'invoice' ]
            shipper_payment_state_invoice_comment = f"{MESSAGE_LANGUAGE_SELECTION[language]['invoice_of_shipper']}: {shipper_payment_state_invoice_comments_list[0]}"  if len(shipper_payment_state_invoice_comments_list) > 0 else MESSAGE_LANGUAGE_SELECTION[language]['without_payment_status']
            
            transporter_payment_state_bill_comments_list = [PAYMENT_STATE_SELECTION[language][line_load["account_move_id"].payment_state] for line_load in records if line_load["account_move_id"] and line_load['move_type'] == 'bill' ]
            transporter_payment_state_bill_comment = f"{MESSAGE_LANGUAGE_SELECTION[language]['invoice_of_shipper']}: {transporter_payment_state_bill_comments_list[0]}" if len(transporter_payment_state_bill_comments_list) > 0 else MESSAGE_LANGUAGE_SELECTION[language]['without_payment_status']


            in_shipper_draft_invoice = self.get_min_date([line_load['account_move_id']['create_date'] for line_load in records if line_load['move_type'] == 'invoice'])
            in_transporter_draft_invoice = self.get_min_date([line_load['account_move_id']['create_date'] for line_load in records if line_load['move_type'] == 'bill'])
            
            
            load_status_obj = {
                "rcv_accounting": {'name': 'rcv_accounting', 'date': rcv_accounting_date, 'description': MESSAGE_LANGUAGE_SELECTION[language]['received_in_accounting'], 'completed': False},
                
                
                  #  => {carga llega odoo y se coloca en el draft},
                "in_shipper_draft_invoice": {'name': 'in_shipper_draft_invoice', 'date': in_shipper_draft_invoice,  'description': MESSAGE_LANGUAGE_SELECTION[language]['in_shipper_draft_invoice'], 'completed': False},
                # {carga llega odoo y se coloca en el draft},
                "in_transporter_draft_invoice": {'name': 'in_transporter_draft_invoice', 'date': in_transporter_draft_invoice, 'description': MESSAGE_LANGUAGE_SELECTION[language]['in_transporter_draft_invoice'], 'completed': False},
                
                # {cuando el borrador pasa a invoice (no es un draft) / cuando se aprueba},
                "in_shipper_approved_invoice": {'name': 'in_shipper_approved_invoice', 'date': created_shipper_invoice_date,  'description': MESSAGE_LANGUAGE_SELECTION[language]['in_shipper_approved_invoice'],  'completed': False},
                    
                # {cuando el borrador pasa a invoice (no es un draft) / cuando se aprueba},
                "in_transporter_approved_invoice": {'name': 'in_transporter_approved_invoice', 'date': created_transporter_invoice_date, 'description': MESSAGE_LANGUAGE_SELECTION[language]['in_transporter_approved_invoice'],  'completed': False},
               
                "created_shipper_invoice": {'name': 'created_shipper_invoice', 'date': created_shipper_invoice_date, 'description': MESSAGE_LANGUAGE_SELECTION[language]['invoiced_shipper'], 'completed': False},
                "created_transporter_invoice": {'name': 'created_transporter_invoice', 'date': created_transporter_invoice_date, 'description': MESSAGE_LANGUAGE_SELECTION[language]['billed_transporter'], 'completed': False},
                "shipper_payment_state_invoice": {'name': 'shipper_payment_state_invoice', 'date': shipper_payment_state_invoice_date, 'description': f"{MESSAGE_LANGUAGE_SELECTION[language]['invoice_of_shipper']}: ({shipper_payment_state_invoice_comment})" , 'completed': False},
                "transporter_payment_state_invoice": {'name': 'transporter_payment_state_invoice', 'date': transporter_payment_state_invoice_date, 'description': f"{MESSAGE_LANGUAGE_SELECTION[language]['bill_transporter']}: ({transporter_payment_state_bill_comment})", 'completed': False},
               
                
                # {cuando en contabilidad registran el pago / concilian pago},
                "paid_by_shipper": {'name': 'paid_by_shipper', 'date': shipper_payment_state_invoice_date, 'description': MESSAGE_LANGUAGE_SELECTION[language]['paid_by_shipper'],  'completed': False},
                    
                # {cuando en contabilidad registran el pago / concilian pago},
                "paid_to_transporter": {'name': 'paid_to_transporter', 'date': transporter_payment_state_invoice_date, 'description': MESSAGE_LANGUAGE_SELECTION[language]['paid_to_transporter'],  'completed': False},
            }
            
            load_status_obj['rcv_accounting']['completed'] = load_status_obj['rcv_accounting']['date'] != None
            load_status_obj['created_shipper_invoice']['completed'] = load_status_obj['created_shipper_invoice']['date'] != None
            load_status_obj['shipper_payment_state_invoice']['completed'] = load_status_obj['shipper_payment_state_invoice']['date'] != None
            load_status_obj['created_transporter_invoice']['completed'] =  load_status_obj['created_transporter_invoice']['date'] != None
            load_status_obj['transporter_payment_state_invoice']['completed'] = load_status_obj['transporter_payment_state_invoice']['date'] != None
            
            load_status_obj['in_shipper_draft_invoice']['completed'] = load_status_obj['in_shipper_draft_invoice']['date'] != None
            load_status_obj['in_transporter_draft_invoice']['completed'] = load_status_obj['in_transporter_draft_invoice']['date'] != None
            load_status_obj['in_shipper_approved_invoice']['completed'] = load_status_obj['in_shipper_approved_invoice']['date'] != None
            load_status_obj['in_transporter_approved_invoice']['completed'] =  load_status_obj['in_transporter_approved_invoice']['date'] != None
            load_status_obj['paid_by_shipper']['completed'] = load_status_obj['paid_by_shipper']['date'] != None
            load_status_obj['paid_to_transporter']['completed'] = load_status_obj['paid_to_transporter']['date'] != None
            
            
            statuses = []
            for load_status in load_status_obj:
                statuses.append(load_status_obj[load_status])
            groups_statuses.append({'sub_load_id': load_id,  'load_details': load_details, 'statuses': statuses})
            
        return groups_statuses