from odoo import models
import logging
_logger = logging.getLogger(__name__)

from xlsxwriter.utility import xl_col_to_name

# PARA MAS DOCUMENTACION SOBRE XLSXWRITER: https://xlsxwriter.readthedocs.io/format.html?highlight=currency#format-set-num-format
class PayslipXlsx(models.AbstractModel):
    _name = 'report.exo_api.report_payslip_name'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, payslip_lines):
        report_name = "Reporte de Salario"
        sheet = workbook.add_worksheet(report_name)
        bold = workbook.add_format({'bold': True})

        row = 2

        sheet.write(row, 0, "Nombre Nómina", bold)
        sheet.write(row, 1, "Empleado", bold)
        sheet.write(row, 2, "Departamento", bold)
        sheet.write(row, 3, "Posicion", bold)
        
        currency_format = workbook.add_format({'font_color': 'black', 'num_format': '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)'})
        cell_format = workbook.add_format({'font_color': 'red', 'num_format': '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)'})

        # Se necesita agrupar por código no por nombre
        columns = {}
        col = 4
        for line in payslip_lines:
            key = line['salary_rule_id']['_excel_rule_name']
            if (not columns.get(key)):
                columns[key] = col
                sheet.write(row, col, key, bold)
                col += 1

        payslips = {}
        for line in payslip_lines:
            key = str(line.slip_id.id)
            if (payslips.get(key)):
                payslips[key]["lines"].append(line)
            else:
                payslips[key] = {"payslip": line.slip_id, "lines": [line]} 
        
        listData = payslips.items()
        for slip_id_key in listData:
            row += 1
            for x in range(col):
                sheet.write(row, x, 0, cell_format)
                
            sheet.write(row, 0, slip_id_key[1]["payslip"]["name"])
            sheet.write(row, 1, slip_id_key[1]["payslip"]["employee_id"]["display_name"])
            sheet.write(row, 2, slip_id_key[1]["payslip"]["employee_id"]['contract_id']["department_id"]['display_name'] if slip_id_key[1]["payslip"]["employee_id"]['contract_id'] and slip_id_key[1]["payslip"]["employee_id"]['contract_id']['department_id'] else 'No Definido')
            sheet.write(row, 3, slip_id_key[1]["payslip"]["employee_id"]['contract_id']["job_id"]['display_name'] if slip_id_key[1]["payslip"]["employee_id"]['contract_id'] and slip_id_key[1]["payslip"]["employee_id"]['contract_id']['job_id'] else 'No Definido' )
           
            for line in slip_id_key[1]["lines"]:
                key = line['salary_rule_id']['_excel_rule_name']
                sheet.write(row, columns[key], line['total'], currency_format)
                
        
        merge_format = workbook.add_format({
            'bold':     True,
            'border':   6,
            'align':    'center',
            'valign':   'vcenter',
            'fg_color': '#D7E4BC',
        })
        sheet.merge_range(0, 0, 1, col - 1, 'REPORTE DE CALCULO SALARIAL', merge_format)

        # Documentation: https://xlsxwriter.readthedocs.io/worksheet.html#set_column. 
        # Se estan seteando de la columna 0 (A) a la Columna 4 E en 32
        sheet.set_column(0, 3, 32)
        sheet.set_column(4, col, 15)
            