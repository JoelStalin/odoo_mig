# -*- coding: utf-8 -*-
import os
import json
import requests
import logging
import datetime
from selectolax.parser import HTMLParser
from lxml import html
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)

class UniqueBenefitDiscountWizard(models.TransientModel):
    _name = 'unique.benefit.discount.wizard'
    _description = 'Fetch Transactions for Unique Benefit Discount'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def fetch_and_process_transactions(self,auto=False):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        def get_viewstate(html_text):
            parser = HTMLParser(html_text)
            viewstate_input = parser.css_first("input#__VIEWSTATE")
            return viewstate_input.attributes['value'] if viewstate_input else None

        def get_value(html_text, field):
            parser = HTMLParser(html_text)
            input_tag = parser.css_first(f"input#{field}")
            return input_tag.attributes['value'] if input_tag else None

        def get_xpath_value(page_tree, xpath_expr):
            values = page_tree.xpath(xpath_expr)
            return values[0].strip() if values else None

        def parse_html_table(html_text):
            doc = html.fromstring(html_text)
            tables = doc.xpath('//table')
            if not tables:
                raise ValidationError("No se encontró ninguna <table> en la respuesta HTML.")

            table = tables[0]
            headers = []
            header_row = table.xpath('.//tr[th]')
            if header_row:
                th_cells = header_row[0].xpath('./th')
                headers = [th.text_content().strip() for th in th_cells]

            data_rows = table.xpath('.//tr[td]')
            table_data = []
            for row in data_rows:
                cells = row.xpath('./td')
                if len(cells) == len(headers) and row == header_row[0]:
                    continue
                row_data = {}
                for i, cell in enumerate(cells):
                    col_name = headers[i] if i < len(headers) else f"col_{i}"
                    cell_text = cell.text_content().strip()
                    row_data[col_name] = cell_text
                table_data.append(row_data)
            return table_data

        with requests.Session() as session:
            session.headers.update(headers)

            login_url = str(os.getenv('MAGYCORP_URL_LOGIN'))
            response = session.get(login_url)
            viewstate = get_value(response.text, "__VIEWSTATE")
            eventvalidation = get_value(response.text, '__EVENTVALIDATION')
            viewstategenerator = get_value(response.text, "__VIEWSTATEGENERATOR")

            login_data = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "__SCROLLPOSITIONX": "0",
                "__SCROLLPOSITIONY": "0",
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "tbuser": str(os.getenv('MAGYCORP_USER')),
                "tbpswd": str(os.getenv('MAGYCORP_PASSWORD')),
                "btlogin": "CONECTARSE"
            }
            session.post(login_url, data=login_data)

            consumos_url = str(os.getenv('CONSUMOS_URL'))
            get_consumo_response = session.get(consumos_url)
            viewstate = get_value(get_consumo_response.text, "__VIEWSTATE")
            eventvalidation = get_value(get_consumo_response.text, '__EVENTVALIDATION')
            viewstategenerator = get_value(get_consumo_response.text, "__VIEWSTATEGENERATOR")

            page = html.fromstring(get_consumo_response.content)
            cbempresa = get_xpath_value(page, "//select[@id='ctl00_ContentPlaceHolder1_cbempresa']/option[@selected='selected']/@value")
            cbsucursal = get_xpath_value(page, "//select[@id='ctl00_ContentPlaceHolder1_cbsucursal']/option[@selected='selected']/@value")
            cbcliente = get_xpath_value(page, "//select[@id='ctl00_ContentPlaceHolder1_cbcliente']/option[@selected='selected']/@value")
            cbusuario = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbusuario"]/option[1]/@value')
            cbgrupo = get_xpath_value(page, "//select[@id='ctl00_ContentPlaceHolder1_cbgrupo']/option[@selected='selected']/@value")
            cbstatus = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbstatus"]/option[1]/@value')
            cbsubgrupo = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbsubgrupo"]/option[1]/@value')
            cbtarjetahabiente = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbtarjetahabiente"]/option[1]/@value')
            cbtipoconsumo = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbtipoconsumo"]/option[1]/@value')
            cbforma = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbforma"]/option[1]/@value')
            cbterminal = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbterminal"]/option[1]/@value')
            cbpagesize = get_xpath_value(page, '//*[@id="ctl00_ContentPlaceHolder1_cbpagesize"]/option[1]/@value')

            fecha1 = self.start_date.strftime('%d-%m-%Y')
            fecha2 = self.end_date.strftime('%d-%m-%Y')

            consumo_data = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btfile_ok_excel",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "__SCROLLPOSITIONX": "0",
                "__SCROLLPOSITIONY": "846",
                "__VIEWSTATEENCRYPTED": "",
                "ctl00$ContentPlaceHolder1$cbempresa": cbempresa or "",
                "ctl00$ContentPlaceHolder1$cbsucursal": cbsucursal or "",
                "ctl00$ContentPlaceHolder1$cbcliente": cbcliente or "",
                "ctl00$ContentPlaceHolder1$cbusuario": cbusuario or "",
                "ctl00$ContentPlaceHolder1$tbfecha1": fecha1,
                "ctl00$ContentPlaceHolder1$tbfecha2": fecha2,
                "ctl00$ContentPlaceHolder1$tbfind": "",
                "ctl00$ContentPlaceHolder1$cbstatus": cbstatus or "",
                "ctl00$ContentPlaceHolder1$cbgrupo": cbgrupo or "",
                "ctl00$ContentPlaceHolder1$cbsubgrupo": cbsubgrupo or "",
                "ctl00$ContentPlaceHolder1$cbtarjetahabiente": cbtarjetahabiente or "",
                "ctl00$ContentPlaceHolder1$cbtipoconsumo": cbtipoconsumo or "",
                "ctl00$ContentPlaceHolder1$cbforma": cbtipoconsumo or "",
                "ctl00$ContentPlaceHolder1$cbterminal": cbterminal or "",
                "ctl00$ContentPlaceHolder1$cbpagesize": cbpagesize or "",
                "ctl00$ContentPlaceHolder1$tbanula_empresa": "",
                "ctl00$ContentPlaceHolder1$tbanula_rncempresa": "",
                "ctl00$ContentPlaceHolder1$tbanula_localidad": "",
                "ctl00$ContentPlaceHolder1$tbanula_numero": "",
                "ctl00$ContentPlaceHolder1$tbanula_fecha": "",
                "ctl00$ContentPlaceHolder1$tbanula_tarjeta": "",
                "ctl00$ContentPlaceHolder1$tbanula_rnc": "",
                "ctl00$ContentPlaceHolder1$tbanula_nombre": "",
                "ctl00$ContentPlaceHolder1$tbanula_monto": "",
                "ctl00$ContentPlaceHolder1$tbanula_tarjetahabiente": "",
                "ctl00$ContentPlaceHolder1$tbanula_motivo": "",
                "ctl00$ContentPlaceHolder1$tbarchivo_nombre": "transaciones",
            }

            post_consumo_response = session.post(consumos_url, data=consumo_data)
            try:
                table_data = parse_html_table(post_consumo_response.text)
            except ValidationError as e:
                raise ValidationError(f"No se pudo parsear la tabla: {str(e)}")

        self._get_filtered_transactions(table_data,auto)

    def _get_filtered_transactions(self, transactions,auto=False):
        product_tmpl = self.env['product.template'].sudo().search([('barcode', '=', 'COMBUSTIBLE')], limit=1)
        if not product_tmpl:
            raise ValidationError("No se encontró product.template con barcode 'COMBUSTIBLE'.")
        analytic_account = self.env['account.analytic.account'].sudo().search([('code', '=', 'COMBUSTIBLE')], limit=1)
        if not analytic_account:
            raise ValidationError("No se encontró account.analytic.account con code 'COMBUSTIBLE'.")
        for tx in transactions:
            identificacion = tx.get('IDENTIFICACION') or tx.get('Documento de identidad') or ''
            if identificacion.endswith('-1'):
                identificacion = identificacion[:-2]
            discount_id = self.env['discount.carrier'].sudo().search([('fuel_card', '=', tx.get('TARJETA'))], limit=1)
            partner_id = discount_id.partner_id if discount_id else None
            if partner_id:
                monto_str = tx.get('MONTO') or '0'
                monto_str = monto_str.replace('$', '').replace(',', '').strip()
                try:
                    monto = float(monto_str)
                except ValidationError:
                    monto = 0.0
                cantidad_str = tx.get('CANTIDAD') or '0'
                try:
                    cantidad = float(cantidad_str)
                except ValidationError:
                    cantidad = 0.0
                transaction_number = tx.get('NÚMERO') or ' '
                producto = tx.get('PRODUCTO') or ' '
                fecha_str = tx.get('FECHA') or fields.Date.today().isoformat()
                fecha = self.parse_and_validate_date(fecha_str)
                discount = []
                discount = self.env['unique.benefit.transaction'].sudo().search([
                    ('tracking', '=', f"{transaction_number} {fecha}")
                ])
                #descuento de 6 por galon
                # monto = monto - (6 * cantidad)
                if not discount:
                      self.env['unique.benefit.transaction'].create({
                        'name': producto,
                        'tracking': f"{transaction_number} {fecha}",
                        'partner_id': partner_id.id,
                        'product_tmpl_id': product_tmpl.id,
                        'analytic_account_id': analytic_account.id,
                        'amount': monto,
                        'product_quantity': cantidad,
                        'transaction_type': 'credit',
                        'transaction_date': fecha,
                        'transaction_json_log': json.dumps(tx, ensure_ascii=False)
                    })
            else:
                _logger.info("\n___________________ No tiene parnert relacionados ___________________\n%s", tx)
        self.env['unique.benefit.transaction'].assign_discount_to_pending_transactions(self.start_date, self.end_date)            
        return
    def parse_and_validate_date(self, fecha_str):
        """Parsea y valida una cadena de fecha a un objeto datetime."""
        if not fecha_str:
            return None  

        formats = [
            "%m/%d/%Y %I:%M:%S %p",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%d-%m-%Y"
        ]

        for fmt in formats:
            try:
                return datetime.datetime.strptime(fecha_str, fmt)
            except ValueError:
                continue 

        try:
            return datetime.datetime.fromisoformat(fecha_str)
        except ValueError:
            pass  

        return False  
        

     
    @api.model
    def schedule_fetch_transactions(self):
        today = fields.Date.today()
        today_date = fields.Date.from_string(today)
        if today_date.day == 16:
            start_date = today_date.replace(day=1)
            end_date = today_date.replace(day=15)
            wizard = self.create({
            'start_date': start_date,
            'end_date': end_date,
            })
            wizard.fetch_and_process_transactions(auto=True)
        elif today_date.day == 1:
            previous_month_last_day = today_date - datetime.timedelta(days=1)
            end_date = previous_month_last_day
            start_date = previous_month_last_day.replace(day=16)
            
            wizard = self.create({
            'start_date': start_date,
            'end_date': end_date,
                })
            wizard.fetch_and_process_transactions()
    

       
        
class UniqueBenefitTransaction(models.Model):
    _name = 'unique.benefit.transaction'
    _description = 'Unique Benefit Transaction'
    _sql_constraints = [
        ('unique_tracking', 'unique(tracking)', "El registro existe. No se permiten duplicados.")
    ]

    name = fields.Text(string='Razón o comentario', required=True)
    discount_id = fields.Many2one('unique.benefit.discount', string="Discount", ondelete="cascade")
    transaction_date = fields.Datetime(string="Transaction Date", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    partner_vat = fields.Char(related='partner_id.vat', string="Identificacion", store=True, readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string="Producto de Referencia", required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta Analítica", required=True)
    product_quantity = fields.Integer("Cantidad", default=1, required=True)
    transaction_type = fields.Selection([('debit', 'Debito'), ('credit', 'Credito')], string="Tipo de Transacción", default='credit', required=True)
    transaction_json_log = fields.Text(string="Transaction JSON Log")
    amount = fields.Float(string="Amount", required=True)
    tracking = fields.Char(string="Tracking")
    json_log = fields.Text(string="JSON Log")

   
    @api.model
    def assign_discount_to_pending_transactions(self, start_date, end_date):
        transactions = self.env['unique.benefit.transaction'].search([
            ('discount_id', '=', False),
            ('transaction_date', '>=', start_date),
            ('transaction_date', '<=', end_date),
        ])

        month_names = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        period_label = f"{start_date.day} - {end_date.day} {month_names[start_date.month]}"

        grouped_transactions = {}
        for transaction in transactions:
            if transaction.partner_id.id not in grouped_transactions:
                grouped_transactions[transaction.partner_id.id] = {
                    'amount': 0,
                    'product_quantity': 0,
                    'transactions': []
                }
            grouped_transactions[transaction.partner_id.id]['amount'] += transaction.amount
            grouped_transactions[transaction.partner_id.id]['transactions'].append(transaction)

        for partner_id, data in grouped_transactions.items():
            for transaction in data['transactions']:
                existing_discount = self.env['unique.benefit.discount'].search([
                    ('partner_id', '=', partner_id),
                    ('move_line_id', '=', False),
                    ('transaction_ids', '=', transaction.id),
                    ('transaction_date', '=', transaction.transaction_date),
                    ('product_quantity', '=', transaction.product_quantity),
                ], limit=1)

            if existing_discount:
                existing_discount.write({
                    'amount': data['amount'],
                    'product_quantity': data['product_quantity'],
                })
            else:
                existing_discount = self.env['unique.benefit.discount'].create({
                    'name': f'{period_label}: {data["transactions"][0].name}',
                    'partner_id': partner_id,
                    'product_tmpl_id': data['transactions'][0].product_tmpl_id.id,
                    'analytic_account_id': data['transactions'][0].analytic_account_id.id,
                    'amount': data['amount'],
                    'product_quantity': 1,
                    'transaction_date': data['transactions'][0].transaction_date,
                    'transaction_type': data['transactions'][0].transaction_type,
                })

            for transaction in data['transactions']:
                transaction.discount_id = existing_discount.id
