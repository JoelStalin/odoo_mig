from odoo.exceptions import ValidationError
from datetime import timedelta, timedelta
import calendar
import logging
_logger = logging.getLogger(__name__)



def get_monthly_dates(date):
    start_date = date.replace(day=1)    
    last_day_month = calendar.monthrange(date.year, date.month)[1]
    end_date = date.replace(day=last_day_month)

    return {'start_date': start_date, 'end_date': end_date}
    
def get_fortnight_dates(date):
    day = date.day
    if day <= 15:
        start_date = date.replace(day=1)
        end_date = date.replace(day=15)
    else:
        last_day_month = calendar.monthrange(date.year, date.month)[1]
        start_date = date.replace(day=16)
        end_date = date.replace(day=last_day_month)
    return {'start_date': start_date, 'end_date': end_date}
    
def get_week_curt(load_date, curt_date):  
    start_date = load_date
    end_date = load_date + timedelta(days=1)
    
    while start_date.weekday() != curt_date.weekday(): 
        start_date -= timedelta(days=1)  
    
    while end_date.weekday() != curt_date.weekday(): 
        end_date += timedelta(days=1)
        
    end_date -= timedelta(days=1)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0) 
    
    return {'start_date': start_date, 'end_date': end_date}


    

def get_invoice_block(partner, load_date):
    load_date = load_date.replace(hour=0, minute=0, second=0, microsecond=0)
    payment_term = partner.load_payment_term_id
    
    if not payment_term:
        raise ValidationError(f"El cliente ({partner.name}) no tiene configurado una Frecuencia de Facturación.")

    if not partner['exo_load_start_date']:
        raise ValidationError(f"El cliente ({partner.name}) no tiene configurado una Fecha de Inicio de la carga..")
    
    curt_date = partner['exo_load_start_date'].replace(hour=0, minute=0, second=0, microsecond=0) 
    
    range_v = None
    if (payment_term['type_freq'] == 'daily'):
        range_v = {
            'start_date': load_date.replace(hour=00, minute=00, second=00, microsecond=0),
            'end_date': load_date.replace(hour=23, minute=59, second=59, microsecond=0) 
        }
        
    if (payment_term['type_freq'] == 'week'):
        range_v = get_week_curt(load_date, curt_date)
    
    if (payment_term['type_freq'] == 'fortnight'):
        range_v = get_fortnight_dates(load_date)
    
    if (payment_term['type_freq'] == 'monthly'):
        range_v = get_monthly_dates(load_date)
    
    if (range_v == None):
        raise ValidationError(f"Al cliente ({partner.name}) no se le pudo crear el bloque de rango de fecha, favor verificar con su proveedor de software")
        
    start_date = range_v['start_date'].replace(hour=5)
    end_date = range_v['end_date'].replace(hour=23)
    code_result = f"bloque-{start_date.strftime('%Y-%m-%d')} -> {end_date.strftime('%Y-%m-%d')}"
    
    return {'code_result': code_result, 'block_start':  start_date, 'block_end': end_date}

def get_orders_in_ids(orders):
        ids = []
        for order in orders:
            ids.append(order['order_num'])
        return ','.join(ids)