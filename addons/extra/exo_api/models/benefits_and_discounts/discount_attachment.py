from odoo import models, fields, api
import base64
import io
import xlsxwriter

class AccountMove(models.Model):
    _inherit = 'account.move'

    def generate_excel_report_Descuentos(self):
        for record in self:
            file_name = f"Reporte_Descuentos_{record.name}.xlsx"
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Descuentos')

            worksheet.write(0, 0, 'Cliente')
            worksheet.write(0, 1, 'Monto')
            worksheet.write(0, 2, 'Fecha')
            worksheet.write(0, 3, 'Cantidad')
            worksheet.write(0, 4, 'Producto')
            worksheet.write(0, 5, 'Cuenta Analítica')
            worksheet.write(0, 6, 'Tipo de Transacción')

            row = 1

            discount_carrier_data = self.env['discount.carrier'].search([('partner_id', '=', record.partner_id.id)])
            for discount in discount_carrier_data:
                worksheet.write(row, 0, discount.partner_id.name)
                worksheet.write(row, 1, discount.discount_parameters_ids.amount)
                worksheet.write(row, 2, str(discount.create_date))
                row += 1

            for line in record.invoice_line_ids:
                unique_benefit_data = self.env['unique.benefit.discount'].search([('move_line_id', '=', line.id)])
                for benefit in unique_benefit_data:
                    worksheet.write(row, 0, benefit.partner_id.name)
                    worksheet.write(row, 1, benefit.amount)
                    worksheet.write(row, 2, str(benefit.transaction_date))
                    worksheet.write(row, 3, benefit.product_quantity)
                    worksheet.write(row, 4, benefit.product_tmpl_id.name)
                    worksheet.write(row, 5, benefit.analytic_account_id.name)
                    worksheet.write(row, 6, benefit.transaction_type)
                    row += 1

            workbook.close()
            output.seek(0)
            file_content = base64.b64encode(output.read())

            attachment_vals = {
                'name': file_name,
                'res_model': 'account.move',
                'res_id': record.id,
                'type': 'binary',
                'datas': file_content,
                'store_fname': file_name,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            self.env['ir.attachment'].create(attachment_vals)

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.generate_excel_report_Descuentos()
        return res