import pytz
from datetime import datetime, timedelta


import logging
_logger = logging.getLogger(__name__)

def get_datetime_in_current_zone(date_time = None):
    validation_time =date_time if date_time else datetime.now() 
    validation_time_localized = pytz.utc.localize(validation_time)
    santo_domingo_tz = pytz.timezone("America/Santo_Domingo")
    dt = validation_time_localized.astimezone(santo_domingo_tz)
    result = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 59, 0)
    return result 

def get_month_start_and_end_dates_from_current(current_date):
    # Obtener el año y el mes de la fecha actual
    year = current_date.year
    month = current_date.month

    # Crear la fecha del primer día del mes
    month_start_date = datetime(year, month, 1)

    # Crear la fecha del primer día del siguiente mes y restar un día
    month_end_date = month_start_date + timedelta(days=32)
    month_end_date = month_end_date.replace(day=1) - timedelta(days=1)

    return month_start_date, month_end_date