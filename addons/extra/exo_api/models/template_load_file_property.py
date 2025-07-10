from ..helpers.template_helper import generate_combinations, get_data_from_json, get_data_to_export, add_subtotals
from ..helpers.excel_helper import generate_excel_file
from ..helpers.pdf_helper import generate_pdf_file
import base64


from odoo import models, fields
from odoo.exceptions import ValidationError

import json
import os
from datetime import timedelta, timedelta, datetime
import logging
_logger = logging.getLogger(__name__)

 # HEADER DE EJEMPLO
 # header = [
        #     {'type': 'compute', 'show': True, 'name': 'Mes', 'order': 1, 'key': 'month', 'value': 'datetime.strptime(data_to_export["createdAt"]["value"], "%Y/%m/%d %H:%M").month'},
        #     {'type': 'compute', 'show': True, 'name': 'Dia', 'order': 2, 'key': 'day', 'value': 'datetime.strptime(data_to_export["createdAt"]["value"], "%Y/%m/%d %H:%M").day'},
        #     {'type': 'normal', 'show': True, 'name': 'Load Number', 'order': 3, 'width': 30, 'key': 'loadNumber'},
        #     {'type': 'normal', 'show': True, 'name': 'No. Orden', 'order': 4, 'key': 'orders.order_num'}, 
        #     {'type': 'normal', 'show': True, 'name': 'Zona', 'order': 5, 'key': 'orders.zone.name'},
        #     {'type': 'normal', 'show': True, 'name': 'Adress', 'order': 6, 'key': 'shipperAddress'}, 
        #     {'type': 'normal', 'show': True, 'name': 'Status', 'order': 7, 'key': 'orders.status'}, 
        #     {'type': 'normal', 'show': True, 'name': 'Tipo Servicio', 'order': 8, 'key': 'serviceOfferingDetails.serviceType'},
        #     {'type': 'normal', 'show': True, 'name': 'Tipo Producto', 'order': 9, 'key': 'serviceOfferingDetails.logisticProductTypes'}, 
        #     {'type': 'normal', 'show': True, 'name': 'Unig Tag', 'order': 10, 'key': 'serviceOfferingDetails.businessUnitTagTypes'},
        #     {'type': 'normal', 'show': True, 'name': 'atTheTimeOfAssigning', 'order': 11, 'key': 'currencyExchange.atTheTimeOfAssigning'}, 
        #     {'type': 'normal', 'show': True, 'name': 'transportCost', 'order': 12, 'key': 'profitability.transportCost'}, 
        #     {'type': 'normal', 'show': True, 'name': 'createdAt', 'order': 13, 'key': 'createdAt'},
        #     {'type': 'normal', 'show': True, 'name': 'revenue', 'order': 14, 'key': 'profitability.revenue'},
        #     {'type': 'compute', 'show': True, 'name': 'Incoming', 'order': 15, 'key': 'incoming_sum', 'value': 'round(data_to_export["currencyExchange.atTheTimeOfAssigning"]["value"] * data_to_export["profitability.revenue"]["value"], 2)'},
        #     {'type': 'compute', 'show': True, 'name': 'Costs', 'order': 16, 'key': 'costs_sum', 'value': 'round(data_to_export["currencyExchange.atTheTimeOfAssigning"]["value"] * data_to_export["profitability.transportCost"]["value"], 2)'},
        #     {'type': 'compute', 'show': True, 'name': 'Diferencia', 'order': 17, 'key': 'profitability_sum', 'value': 'round(data_to_export["incoming_sum"]["value"] - data_to_export["costs_sum"]["value"], 2)'},
            #     {'type': 'compute', 'show': True, 'name': 'MB%', 'order': 18, 'key': 'mb', 'value': 'round(data_to_export["profitability_sum"]["value"] / data_to_export["incoming_sum"]["value"], 2)'},
        # ]
from reportlab.lib.pagesizes import A0, A1, A10, A2, A3, A4, A5, A6, A7, A8, A9, B0, B1, B10, B2, B3, B4, B5, B6, B7, B8, B9, C0, C1, C10, C2, C3, C4, C5, C6, C7, C8, C9, ELEVENSEVENTEEN, GOV_LEGAL, GOV_LETTER, HALF_LETTER, JUNIOR_LEGAL, LEDGER , LEGAL, LETTER, TABLOID
pageSize = {
    'A0': A0, 'A1': A1, 'A10': A10, 'A2': A2, 'A3': A3, 'A4': A4, 'A5': A5, 'A6': A6, 'A7': A7, 'A8': A8, 'A9': A9, 'B0': B0, 'B1': B1, 'B10': B10, 'B2': B2, 'B3': B3, 'B4': B4, 'B5': B5, 'B6': B6, 'B7': B7, 'B8': B8, 'B9': B9, 'C0': C0, 'C1': C1, 'C10': C10, 'C2': C2, 'C3': C3, 'C4': C4, 'C5': C5, 'C6': C6, 'C7': C7, 'C8': C8, 'C9': C9, 'ELEVENSEVENTEEN': ELEVENSEVENTEEN, 'GOV_LEGAL': GOV_LEGAL, 'GOV_LETTER': GOV_LETTER, 'HALF_LETTER': HALF_LETTER, 'JUNIOR_LEGAL': JUNIOR_LEGAL, 'LEDGER': LEDGER , 'LEGAL': LEGAL, 'LETTER': LETTER, 'TABLOID': TABLOID
}
class template_load_file_property(models.Model):
    _name = 'template.load.file.property'
    _description = 'Plantilla para exportar las cargas de EXO'
    
    name = fields.Char("Nombre de la plantilla", required=True, copy=True)
    
    type = fields.Selection([('excel', 'Excel'), ('pdf', 'PDF')], string='Tipo de Plantilla', copy=True, required=True)
    
    is_internal = fields.Boolean("Es una plantilla interna", default=True, required=True)
    
    apply_for_all_shippers = fields.Boolean("Aplicar para todos los shippers", default=False, required=True)
    
    apply_for_all_providers = fields.Boolean("Aplicar para todos los proveedores", default=False, required=True)
    
    pdf_page_size = fields.Selection([('A0', 'A0'), ('A1', 'A1'), ('A10', 'A10'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'), ('A5', 'A5'), ('A6', 'A6'), ('A7', 'A7'), ('A8', 'A8'), ('A9', 'A9'), ('B0', 'B0'), ('B1', 'B1'), ('B10', 'B10'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'), ('B5', 'B5'), ('B6', 'B6'), ('B7', 'B7'), ('B8', 'B8'), ('B9', 'B9'), ('C0', 'C0'), ('C1', 'C1'), ('C10', 'C10'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'), ('C5', 'C5'), ('C6', 'C6'), ('C7', 'C7'), ('C8', 'C8'), ('C9', 'C9'), ('ELEVENSEVENTEEN', 'ELEVENSEVENTEEN'), ('GOV_LEGAL', 'GOV_LEGAL'), ('GOV_LETTER', 'GOV_LETTER'), ('HALF_LETTER', 'HALF_LETTER'), ('JUNIOR_LEGAL', 'JUNIOR_LEGAL'), ('LEDGER', 'LEDGER'), ('LEGAL', 'LEGAL'), ('LETTER', 'LETTER'), ('TABLOID', 'TABLOID')], string='Size de la plantilla PDF', copy=True, default='A2', attrs={'invisible': [('type', '!=', 'pdf')], 'required': [('type', '=', 'pdf')]})
    
    pdf_font_size = fields.Integer('Tamaño del Font para el PDF', copy=True, default=7, attrs={'invisible': [('type', '!=', 'pdf')], 'required': [('type', '=', 'pdf')]  })

    load_file_property = fields.One2many('load.file.property', 'template_id', string='Propiedades', copy=True, required=True)
    
    file = fields.Binary("Archivo", copy=False, attachment=True)
    
    def get_template_file(self, write_file = True, json_data = None):
        load_file_property = self.load_file_property.filtered(lambda line: line.is_active == True)
        if (not load_file_property or len(load_file_property) == 0):
            raise ValidationError("Debe tener al menos una propiedad definida.")
        
        header = []
        for property in load_file_property:
            header.append({'type': property['type'], 'calculation_mode': property['calculation_mode'], 'duplicate_with_sub_list': property['duplicate_with_sub_list'], 'show': property['show'], 'name': property['name'], 'order': property['order'], 'key': property['key'], 'value': property['value']})
        
        
        data = get_data_to_export(json_data, header) if json_data else get_data_from_json(header)
        formatted_data = []
        for load in data:
            formatted_data += generate_combinations(load)
        add_subtotals(formatted_data)
        binary_buffer = None
        if (not self.type):
            raise ValidationError("Debe especificar un tipo")
        
        if (self.type == 'excel'):
            binary_buffer = generate_excel_file(header, formatted_data)
        else:
            binary_buffer = generate_pdf_file(header, formatted_data,  self.pdf_font_size,pageSize[self.pdf_page_size])
    
        if (write_file):
            self.write({'file': base64.b64encode(binary_buffer.getvalue())})
        return base64.b64encode(binary_buffer.getvalue())
        