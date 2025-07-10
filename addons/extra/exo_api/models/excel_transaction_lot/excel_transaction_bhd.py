from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ReportXlsx(models.AbstractModel):
    _name = 'report.exo_api.excel_transaction_bhd'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, account_batch_payment):
        # 🧠 Diccionarios para cachear búsquedas
        partner_bank_map = {}        # partner_id → bank_account
        partners_without_banks = {}  # partner_id → partner_name

        # ▶️ Fase 1: recolectar cuentas BHD y cachear
        for record in account_batch_payment:
            for payment in record.payment_ids:
                partner = payment.partner_id or (payment.partner_ids and payment.partner_ids[0])
                if not partner or partner.id in partner_bank_map or partner.id in partners_without_banks:
                    continue

                bank_account = self.env['bank.account.dominicana'].search([
                    ('partner_id', '=', partner.id),
                    ('active', '=', True)
                ], limit=1)

                if bank_account and bank_account.bank_code == 'BHD' and bank_account.account_number:
                    partner_bank_map[partner.id] = bank_account
                elif bank_account and bank_account.bank_code != 'BHD' and bank_account.account_number: 
                    continue # Omitir cuentas que no son BHD        
                else:
                    partners_without_banks[partner.id] = partner.name

        # ▶️ Alerta si **algunos** beneficiarios no tienen cuenta BHD
        if partners_without_banks:
            partner_names = '\n'.join(partners_without_banks.values())
            raise ValidationError(_(
                "Los siguientes beneficiarios no tienen cuentas bancarias BHD configuradas:\n%s"
            ) % partner_names)
            
        # ▶️ Escritura del archivo (se omiten pagos de partners sin cuenta)
        sheet = workbook.add_worksheet('transactio')
        bold = workbook.add_format({'bold': True})

        headers = [
            'Tipo de abono', 'Beneficiario', 'Monto',
            'Referencia transacción', 'Descripción', 'Tipo de cuenta',
            'No. de cuenta', 'Correo beneficiario',
            'Fax beneficiario', 'Referencia débito'
        ]
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, bold)

        row = 1
        for record in account_batch_payment:
            _logger.info("🔵 Procesando lote ID=%s, Nombre=%s", record.id, record.name)
            for payment in record.payment_ids:
                partner = payment.partner_id or (payment.partner_ids and payment.partner_ids[0])
                if not partner or partner.id not in partner_bank_map:
                    continue

                bank_account = partner_bank_map[partner.id]
                # Datos a exportar
                acc_holder_name = bank_account.acc_holder_name or ''
                account_number  = bank_account.account_number or ''
                product_type    = bank_account.account_type or ''
                amount          = payment.amount or 0.0
                reference       = payment.ref or ''
                description     = payment.display_name or ''
                email           = partner.email or ''
                phone           = partner.phone or ''

                # Escribir fila
                sheet.write(row, 0, '1')
                sheet.write(row, 1, acc_holder_name)
                sheet.write(row, 2, amount)
                sheet.write(row, 3, '')
                sheet.write(row, 4, reference)
                sheet.write(row, 5, product_type)
                sheet.write(row, 6, account_number)
                sheet.write(row, 7, email)
                sheet.write(row, 8, phone)
                sheet.write(row, 9, '')

                _logger.info("🟢 Fila %s escrita para partner %s", row, acc_holder_name)
                row += 1
