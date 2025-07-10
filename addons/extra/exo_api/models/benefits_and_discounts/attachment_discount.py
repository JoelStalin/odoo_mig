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

            row = 0
            worksheet.write(row, 0, f'Numero de la Factura: {record.name}')
            row = 1
            headers = ['Cliente', 'Monto', 'Fecha', 'Cantidad', 'Producto', 'Cuenta Analítica', 'Tipo de Transacción', 'Factura']
            for col, header in enumerate(headers):
                worksheet.write(row, col, header)

            row += 1
            worksheet.write(row, 0, '---Descuentos Mensuales Aplicados---')
            row += 1
            line_product_ids = record.invoice_line_ids.mapped('product_id.id')
            partner_benefit_discounts = self.env['partner.benefit.discount'].search([('partner_id', 'in', record.partner_id.id)])
            unique_benefit_discounts = self.env['unique.benefit.discount'].search([
                ('product_tmpl_id', 'in', line_product_ids),
                ('move_line_id', '=', record.id),
                ('partner_id', '=', record.partner_id.id)
            ])

            monthly_discounts = {(d.partner_id.id): d for d in partner_benefit_discounts}
            unique_discounts = {(d.product_tmpl_id.id): d for d in unique_benefit_discounts}

            for line in record.invoice_line_ids:
                if line.product_id.id in monthly_discounts:
                    discount = monthly_discounts
                    worksheet.write(row, 0, discount.partner_id.name)
                    worksheet.write(row, 1, line.price_subtotal)
                    worksheet.write(row, 3, line.quantity)
                    worksheet.write(row, 4, line.product_id.name)
                    worksheet.write(row, 5, discount.analytic_account_id.name)
                    row += 1

                if line.product_id.id in unique_discounts:
                    discount = unique_discounts[line.product_id.id]
                    worksheet.write(row, 0, discount.partner_id.name)
                    worksheet.write(row, 1, line.price_subtotal)
                    worksheet.write(row, 2, str(discount.transaction_date))
                    worksheet.write(row, 3, line.quantity)
                    worksheet.write(row, 4, line.product_id.name)
                    worksheet.write(row, 5, discount.analytic_account_id.name)
                    worksheet.write(row, 6, discount.transaction_type)
                    worksheet.write(row, 7, record.name)
                    row += 1

                    if discount.product_tmpl_id.barcode == 'COMBUSTIBLE':
                        row += 1
                        worksheet.write(row, 0, '---Detalle transaciones Combustible---')
                        row += 1

                        unique_transactions = self.env['unique.benefit.transaction'].search([
                            ('partner_id', '=', discount.partner_id.id),
                            ('transaction_date', '=', discount.transaction_date),
                        ])

                        for transaction in unique_transactions:
                            worksheet.write(row, 0, transaction.name)
                            worksheet.write(row, 1, transaction.amount)
                            worksheet.write(row, 2, str(transaction.transaction_date))
                            worksheet.write(row, 3, transaction.product_quantity)
                            worksheet.write(row, 4, transaction.product_tmpl_id.name)
                            worksheet.write(row, 5, transaction.analytic_account_id.name)
                            worksheet.write(row, 6, transaction.transaction_type)
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