from datetime import datetime
from openpyxl import Workbook
from io import BytesIO
from odoo import http
from odoo.http import request, content_disposition

def generate_excel_file(header, body):
    
    # Filtrar las columnas que deben mostrarse
    header_show_true = [cabecera for cabecera in header if cabecera['show']]

    header_sorted = sorted(header_show_true, key=lambda x: x['order'])
    # Crear un nuevo libro de trabajo
    wb = Workbook()

    # Acceder a la hoja activa (por defecto es la primera hoja)
    sheet = wb.active

    # Escribir las cabeceras en la primera fila
    for col_num, cabecera in enumerate(header_sorted, start=1):
        sheet.cell(row=1, column=col_num, value=cabecera['name'])

    # Escribir los datos en las filas siguientes
    for fila_datos in body:
        sheet.append(fila_datos)

        
    excel_buffer = BytesIO()
    
    wb.save(excel_buffer)
    
    excel_buffer.seek(0)
    
    return excel_buffer
   