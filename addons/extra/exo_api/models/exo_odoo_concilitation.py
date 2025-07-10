from odoo import models, fields, http, api
from datetime import datetime
import collections.abc
import threading
import requests
import time
from ..helpers.util_helper import first

from odoo.exceptions import ValidationError
import os
import logging
_logger = logging.getLogger(__name__)


class ExoOdooConciliation(models.Model):
    _name = "exo.odoo.conciliation"
    _description = 'Conciliacion entre EXO y Odoo'

    load_id = fields.Text(string = 'Load Id', required=True)
    load_number = fields.Text(string = 'Load Number', required=True)
    shipper = fields.Text(string = 'Shipper', required=False)
    companyTransporter = fields.Text(string = 'Transportista', required=False)
    createdAt = fields.Date(string='Created At')
    load_status = fields.Text(string = 'Estado carga en EXO', required=False)
    shipper_account_line_load_id = fields.Many2one('account.line.load', 'Shipper Odoo - EXO LOAD',  ondelete='cascade')
    provider_account_line_load_id = fields.Many2one('account.line.load', 'Provider Odoo - EXO LOAD', ondelete='cascade')
    shipper_load_status = fields.Text(string = 'Shipper Estado Odoo', compute="compute_odoo_load_status", store=True)
    provider_load_status = fields.Text(string = 'Proveedor Estado Odoo', compute="compute_odoo_load_status", store=True)

    @api.depends('provider_account_line_load_id.account_move_id.payment_state', 'shipper_account_line_load_id.account_move_id.payment_state')
    def compute_odoo_load_status(self):
        for record in self:
            record.shipper_load_status = 'Sin Estado'
            record.provider_load_status = 'Sin Estado'
            
            if (record.shipper_account_line_load_id):
                record.shipper_load_status = record.shipper_account_line_load_id.account_move_id.payment_state
            
            if (record.provider_account_line_load_id):
                record.provider_load_status = record.provider_account_line_load_id.account_move_id.payment_state
                
    
    def generate_conciliation(self):
        http.request.env['account.load.error'].sudo().with_company(http.request.env.company).create({
            'name': f"EXO Conciliacion",
            'account_load_client_id': http.request.env.user.partner_id.id,
            'partner_type': 'Interno',
            'start_date': datetime.now(),
            'end_date': datetime.now(),
            'message_error': "Inicio de Proceso para Actualizar el Reporte de Conciliacion",
            'current_date': datetime.now(),
            'state': 'draft'
        })
        http.request.env.cr.commit()
        self.start_conciliation()
        return  {'type': 'ir.actions.client', 'tag': 'reload'}
     
        
    def update_odoo_status(self):
        _logger.info("____________________________ACTUALIZANDO ___________STATUS ++++")
        records =  http.request.env['exo.odoo.conciliation'].sudo().search(['|', ('shipper_account_line_load_id', '=', False), ('provider_account_line_load_id', '=', False)])
        index = 0
        for record in records:
            index += 1
            move_lines = http.request.env['account.line.load'].sudo().search([('load_id', 'ilike', record.load_id)])
            if (move_lines):
                _logger.info(f"____________________________ ACTUALIZANDO LINE {index} __________________")
                shipper_line_id = first([move_line['id'] for move_line in move_lines if move_line['move_type'] == 'invoice']) 
                provider_line_id = first([move_line['id'] for move_line in move_lines if move_line['move_type'] == 'bill'])
                
                if (record.shipper_account_line_load_id != shipper_line_id or record.provider_account_line_load_id != provider_line_id):
                    record.sudo().write({
                        'shipper_account_line_load_id': shipper_line_id,
                        'provider_account_line_load_id': provider_line_id,
                    })
                if (index >= 20):
                    http.request.env.cr.commit()
                    index = 0
        _logger.info(f"____________________________ FIN DE ACTUALIZACION DE LINEA __________________")
        
        http.request.env['account.load.error'].sudo().with_company(http.request.env.company).create({
            'name': f"EXO Conciliacion",
            'account_load_client_id': http.request.env.user.partner_id.id,
            'partner_type': 'Interno',
            'start_date': datetime.now(),
            'end_date': datetime.now(),
            'message_error': "Actualizando Estados de Odoo",
            'current_date': datetime.now(),
            'state': 'draft'
        })
        http.request.env.cr.commit()
        

    
    
    def start_conciliation(self):
        self.remove_conciliation_records(False)
        http.request.env['account.load.error'].sudo().with_company(http.request.env.company).create({
            'name': f"EXO Conciliacion",
            'account_load_client_id': http.request.env.user.partner_id.id,
            'partner_type': 'Interno',
            'start_date': datetime.now(),
            'end_date': datetime.now(),
            'message_error': "Records Eliminados",
            'current_date': datetime.now(),
            'state': 'draft'
        })
        http.request.env.cr.commit()

        
        _logger.info("GENERANDO CONCILIATION ")
        
        take = 490
        skip = take * -1
        while (True):
            skip += take
            url = str(os.getenv('HOST_EXO')) + '/exo/loads/filterConsolidated/?skip='+ str(skip) + '&take=' + str(take) + '&useTimeSlot=true&query={}'
            headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache", "api-key": os.getenv('EXO_API_KEY')}
            _logger.info(url)
            _logger.info(headers)
            time.sleep(1)

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise ValidationError('La carga no pudo ser procesada. 1. \nCode: %s\nContent: %s' % (response.status_code, response.content))

            result = response.json()

            if (not isinstance(result, collections.abc.Sequence) and result["loads"] and result["loads"]["Success"] == False):
                _logger.info("____________________________________STEP 7.5.20  _______________________________________________")
                _logger.error('La carga no pudo ser procesada. 2. \nCode: %s\nContent: %s' % (response.status_code, response.content))
                raise ValidationError("La carga no pudo ser procesada.3. Favor comuniquese con su administrador e intente mas tarde")
            _logger.info("____________________________________STEP 7.5.21  _______________________________________________")

            data = result['loads']['Result']['data']
            if (len(data) == 0):
                break
            batch_size = 20
            r = range(0, len(data), batch_size)
            for i in r:
                load_batched = data[i: i + batch_size]
                self.create_many_records(load_batched)

        self.remove_conciliation_records()
        http.request.env['account.load.error'].sudo().with_company(http.request.env.company).create({
            'name': f"EXO Conciliacion",
            'account_load_client_id': http.request.env.user.partner_id.id,
            'partner_type': 'Interno',
            'start_date': datetime.now(),
            'end_date': datetime.now(),
            'message_error': "Records Duplicados Eliminiados",
            'current_date': datetime.now(),
            'state': 'draft'
        })
        http.request.env.cr.commit()
        
        self.get_odoo_loads_not_in_exo()
        self.update_odoo_status()
        
        http.request.env['account.load.error'].sudo().with_company(http.request.env.company).create({
            'name': f"EXO Conciliacion",
            'account_load_client_id': http.request.env.user.partner_id.id,
            'partner_type': 'Interno',
            'start_date': datetime.now(),
            'end_date': datetime.now(),
            'message_error': "Proceso Finalizado",
            'current_date': datetime.now(),
            'state': 'draft'
        })
        
    def remove_conciliation_records(self, only_duplicated = True):
        query = """ DELETE FROM exo_odoo_conciliation """
                
        if (only_duplicated):
            query += """
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM exo_odoo_conciliation
                    GROUP BY load_id
                )
            """
        try:
            if not only_duplicated:
                self.search([]).unlink()
            else:
                # Optimized approach to find and unlink duplicates
                self.env.cr.execute("""
                    DELETE FROM exo_odoo_conciliation
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM exo_odoo_conciliation
                        GROUP BY load_id
                    );
                """)
                # Invalidate cache for the model
                self.invalidate_model(['load_id'])

        except Exception as e:
            _logger.error(f"Error removing conciliation records: {e}")
            raise ValidationError(f"No se pudo procesar la eliminación de registros de conciliación: {e}")
    

    def create_many_records(self, load_batched):
        load_records = [{'load_id': load['_id'], 'load_number': load['loadNumber'],'shipper': load['shipper'],'companyTransporter': load['companyTransporter'],'createdAt': load["loadingStatus"]["slotStartTime"],'load_status': load['load_status']  } for load in load_batched]
        http.request.env['exo.odoo.conciliation'].sudo().create(load_records)
        http.request.env['account.load.error'].sudo().with_company(http.request.env.company).create({
            'name': f"EXO Conciliacion",
            'account_load_client_id': http.request.env.user.partner_id.id,
            'partner_type': 'Interno',
            'start_date': datetime.now(),
            'end_date': datetime.now(),
            'message_error': "Cargando Records",
            'current_date': datetime.now(),
            'state': 'draft'
        })
        http.request.env.cr.commit()


    def get_odoo_loads_not_in_exo(self):
        query = """
            SELECT LEFT(load_id, 24), load_number, shipper  FROM account_line_load
            WHERE LEFT(load_id, 24) NOT IN (SELECT LEFT(load_id, 24) FROM exo_odoo_conciliation)
        """
        try:
            # Direct SQL read for performance/complexity of subquery.
            # This should be reviewed if access rights or other ORM benefits become critical here.
            self._cr.execute(query)
            result = self._cr.fetchall()
            data = [{'load_id': row[0], 'load_number': row[1], 'shipper': row[2]} for row in result]
            load_records = [{'load_id': line.get('load_id'), 'load_number': line.get('load_number'),'shipper': line.get('shipper'), 'companyTransporter': None, 'createdAt': None, 'load_status': None  } for line in data]
            if load_records:
                self.env['exo.odoo.conciliation'].sudo().create(load_records)
            
            self.env['account.load.error'].sudo().with_company(self.env.company).create({
                'name': f"EXO Conciliacion - Odoo Loads not in EXO",
                'account_load_client_id': self.env.user.partner_id.id,
                'partner_type': 'Interno',
                'start_date': datetime.now(),
                'end_date': datetime.now(),
                'message_error': f"Found {len(load_records)} Odoo loads not present in EXO conciliation table.",
                'current_date': datetime.now(),
                'state': 'draft'
            })
            self.env.cr.commit()
                
        except Exception as e:
            _logger.error(f"Error getting Odoo loads not in EXO: {e}")
            raise ValidationError(f"No se pudo obtener las cargas de Odoo no presentes en la conciliación de EXO: {e}")