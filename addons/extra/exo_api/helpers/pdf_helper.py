
from reportlab.lib.pagesizes import A2 as PageSize
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

from datetime import datetime
from io import BytesIO

def generate_pdf_file(header, body, fontsize = 7, pagesize = PageSize):
    pdf_buffer = BytesIO()

    header_show_true = [cabecera for cabecera in header if cabecera['show']]
    header_sorted = sorted(header_show_true, key=lambda x: x['order'])


    # Crear el objeto PDF con tamaño de página legal
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=pagesize)
    # Extraer los títulos y anchos de las columnas del header
    column_titles = [col['name'] for col in header_sorted if col['show']]
        
    # Unir los títulos y datos
    data = [column_titles] + body

    # Crear la tabla con anchos de columna personalizados
    table = Table(data)

    # Establecer estilos de tabla
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), fontsize),
                        
                        
                        ])

    table.setStyle(style)

    # Agregar la tabla al documento PDF
    pdf.build([table])
    return pdf_buffer
