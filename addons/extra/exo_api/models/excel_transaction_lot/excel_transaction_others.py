from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ReportXlsx(models.AbstractModel):
    _name = 'report.exo_api.excel_transaction_others'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, account_batch_payment):
        sheet = workbook.add_worksheet('transactio')
        bold = workbook.add_format({'bold': True})

        headers = [
            'Número de cuenta', 'Código Swift del Banco', 'Tipo de Cuenta',
            'Beneficiario', 'Tipo de movimiento', 'Monto', 'Número de referencia',
            'Descripción', 'Correo electrónico', 'Teléfono', 'Tipo de Identificación',
            'No. de Identificación'
        ]
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, bold)

        row = 1
        partner_bank_map = {}      # cache de cuentas por partner
        partners_without_banks = {}

        # ▶️ Fase 1: cachear todas las cuentas que no sean BHD
        for record in account_batch_payment:
            for payment in record.payment_ids:
                partner = payment.partner_id or (payment.partner_ids and payment.partner_ids[0])
                if not partner or partner.id in partner_bank_map or partner.id in partners_without_banks:
                    continue

                bank_account = self.env['bank.account.dominicana'].search([
                    ('partner_id', '=', partner.id),
                    ('active', '=', True)
                ], limit=1)

                if bank_account and bank_account.bank_code != 'BHD' and bank_account.account_number:
                    partner_bank_map[partner.id] = bank_account
                elif bank_account and bank_account.bank_code == 'BHD' and bank_account.account_number:
                    continue  # Omitir cuentas que son BHD        
                else:
                    partners_without_banks[partner.id] = partner.name

        # ▶️ Si hay beneficiarios sin cuenta configurada, notificar pero continuar
        if partners_without_banks:
            partner_names = '\n'.join(partners_without_banks.values())
            raise ValidationError(_(
                "Los siguientes beneficiarios no tienen cuentas bancarias BHD configuradas:\n%s"
            ) % partner_names)
            
    
        # ▶️ Fase 3: escritura de filas (omitiendo a quienes no tienen cuenta)
        for record in account_batch_payment:
            _logger.info("🔵 Procesando lote ID=%s, Nombre=%s", record.id, record.name)
            for payment in record.payment_ids:
                partner = payment.partner_id or (payment.partner_ids and payment.partner_ids[0])
                if not partner or partner.id not in partner_bank_map:
                    continue

                bank_account   = partner_bank_map[partner.id]
                acc_number     = bank_account.account_number or ''
                bank_bic       = bank_account.swift_code or ''
                product_type   = bank_account.account_type or ''
                acc_holder     = bank_account.acc_holder_name or ''
                amount         = payment.amount or 0.0
                reference      = payment.ref or ''
                description    = payment.display_name or ''
                email          = partner.email or ''
                phone          = partner.phone or ''

                # === Cálculo de Tipo de Identificación ===
                doc_type = (bank_account.document_type or '').strip()
                if doc_type == 'CÉDULA':
                    id_type_char = 'C'
                elif doc_type == 'RNC':
                    id_type_char = 'R'
                else:
                    id_type_char = (bank_account.document_type or '').upper()
                # ================================================

                vat = partner.vat or ''

                sheet.write(row, 0, acc_number)
                sheet.write(row, 1, bank_bic)
                sheet.write(row, 2, product_type)
                sheet.write(row, 3, acc_holder)
                sheet.write(row, 4, 'C')  # Tipo movimiento fijo
                sheet.write(row, 5, amount)
                sheet.write(row, 6, '')
                sheet.write(row, 7, reference)
                sheet.write(row, 8, email)
                sheet.write(row, 9, phone)
                sheet.write(row, 10, id_type_char)
                sheet.write(row, 11, vat)

                _logger.info(
                    "🟢 Fila %s | Partner: %s | Cuenta: %s | Banco: %s | ID Type: %s",
                    row, acc_holder, acc_number, bank_bic, id_type_char
                )
                row += 1
