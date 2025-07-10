from ...helpers.request_helper import post_request_exo

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import datetime
import os
import logging
_logger = logging.getLogger(__name__)


class partner_benefit_discount(models.Model):
    _name="partner.benefit.discount"
    
    name = fields.Char(compute="_compute_name", required=False, copy=False, store=True)
    partner_id = fields.Many2one('res.partner', string="Proveedor", required=True, domain=lambda self: [('internal_partner_type','=', 'transporter')])
    product_quantity = fields.Integer("Cantidad", default=1, required=True)
    benefit_discount_id = fields.Many2one('benefit.discount', string="Beneficio y/o descuento", required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    analytic_tag_ids = fields.Many2many(comodel_name='account.analytic.tag', string='Analytic Tag')
    field_test = fields.Char("MyFieldTest")
    carrier_ids = fields.Many2one('discount.carrier', string="Transportista")
    @api.depends("partner_id", "benefit_discount_id", "field_test")
    def _compute_name(self):
        for record in self:
            _logger.info("_________ test")
            _logger.info(record.field_test)
            record.name = f"{record.partner_id.name}/{record.benefit_discount_id.name}"

class ResPartnerObject(models.Model):
    _name = "res.partner.object"
    _description = "Res Partner Object Id"
    
    partner_id = fields.Many2one('res.partner', string="Transportista", required=True, domain=lambda self: [('internal_partner_type','=', 'transporter')], ondelete="cascade")
    name = fields.Char("Id del Transportista")
    description = fields.Text("Descripción o Nombre del Transportista")
    active = fields.Boolean("Active", default=True)

class partner_inherit(models.Model):
    _inherit = "res.partner"
    _sql_constraints = [
        ('unique_vat', 'unique(vat)', "El registro existe. No se permiten duplicados.")
    ]
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        tracking=True,
        default=lambda self: self.env.company
    )
    analytic_tag_ids = fields.One2many('res.partner.tag', 'partner_id', string='Etiquetas Analíticas')
    exo_load_configurations = fields.One2many('exo.partner.load.configuration', 'partner_id', 'Configuracion de Facturas', help="Define los campos que se visualizaran en la factura del cliente.")
    exo_load_start_date = fields.Datetime(string="Fecha inicial para cargar las facturas de EXO",  tracking=True, required=False, help="Este campo le indica a la acción (Crear y/o actualizar facturas) del modulo de Accounting que solo no permita cargar facturas menores a esta fecha inicial", default=lambda self: datetime(2024, 7, 1, 0, 0, 0))
    benefit_discount_ids = fields.One2many('partner.benefit.discount', 'partner_id', tracking=True, string='Beneficios y descuentos Mensuales de clientes')
    vat = fields.Char(string="Tax ID", help="The Tax Identification Number. ", tracking=True, required=True, unique=True)
    load_statuses = fields.Many2many('partner.load.status', string="Estados a filtrar en EXO", tracking=True)
    search_by_warehouse = fields.Boolean('Permite la busqueda por warehouse a este cliente', tracking=True, default=False )
    create_by_automatic_load = fields.Boolean('Permite que a este cliente se le creen facturas internamente a media noche.', tracking=True, default=False )
    group_by_payment_term = fields.Boolean('Permite que la factura se pueda agrupar por Frecuencia de Facturación', tracking=True, default=True )
    group_by_warehouse = fields.Boolean('Permite que la factura se pueda agrupar por warehouse', tracking=True, default=True )
    rounded_money = fields.Boolean(string="Permite que los precios se redondeen a entero", tracking=True, default = True)
    load_payment_term_id = fields.Many2one('load.payment.term', string="Frecuencia de Facturación", required=False, tracking=True, help="Identica en que periodo un cliente recibira sus facturas. Ej: Cada 7 días, 15 días, 30 días, 60 días, etc.")
    templates_load_files = fields.Many2many('template.load.file.property', tracking=True, string="Plantillas para adjuntar a la factura")
    transform_vehicle_type = fields.Boolean('Convertir el truck Type (35T 75M3 => Cabezote)', tracking=True, default=False )
    group_account_line_by_order = fields.Char('Campo de la orden para agrupar las cargas', tracking=True, default='' )
    tax_products = fields.Many2many('tax.additional.product', tracking=True, string="Impuestos adicionales por producto")
    insurance_percent = fields.Float('Seguro de Carga', tracking=True, default = 0.02)
    apply_other_deductions = fields.Boolean('Aplicar Impuesto (Otras Retenciones 2%).', default=False, tracking=True)
    in_transporter_show_order_num = fields.Boolean('Mostrar en el transportista el numero de orden.', tracking=True, default=False)
    invoice_price_formula = fields.Text(string="Formula de Factura Shipper", default="current_exo_load['profitability']['revenue'] * current_exo_load['currencyExchange']['atTheTimeOfAssigning']", required=True)
    bill_price_formula = fields.Text(string="Formula de Factura Proveedor", default="current_exo_load['profitability']['transportCost'] * current_exo_load['currencyExchange']['atTheTimeOfAssigning']", required=True)
    document_type = fields.Selection([('c', 'CEDULA'), ('r', 'RNC'), ('p', 'PASAPORTE')], string='Tipo de Documento', required=True)
    last_payment_id = fields.Many2one('account.payment', string='Último Pago', compute='_compute_last_payment', store=True)
    internal_partner_type = fields.Selection([('not_defined', 'No Definido'), ('shipper', 'Shipper'), ('transporter', 'Transportista'), ('service', 'Servicios')], string='Tipo de Contacto')
    partner_object_ids = fields.One2many('res.partner.object', 'partner_id', string='Object Ids del Transportista')
    bank_account_ids = fields.One2many(
         'bank.account.dominicana',
         'partner_id',
         string='Cuentas Bancarias RD'
     )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Supongamos que quieres solo los estados activos:
        status_ids = self.env['partner.load.status'].sudo().search([('name', 'in', ["Waiting For CLC approval", "CLC Approved", "In Accounting"])]).ids

        # Asegúrate de asignar una tupla Many2many (6, 0, ids)
        res['load_statuses'] = [(6, 0, status_ids)]
        return res
   
    @api.onchange('vat')
    def _onchange_vat(self):
        if self.vat:
            self.vat = self.vat.replace("-", "").replace('\t', '').replace(' ', '')
            self.document_type = 'c' if len(self.vat) == 11 else 'r'

    
    @api.onchange('internal_partner_type')
    def _onchange_internal_partner_type(self):
        if self.internal_partner_type == 'transporter' :
            self.create_by_automatic_load = True
            self.group_by_payment_term = True
            self.group_by_warehouse = False
            self.rounded_money = True
            self.apply_other_deductions = True
            if not self.insurance_percent or self.insurance_percent == 0:
                self.insurance_percent = 0.02
                
            if not self.load_payment_term_id:
                self.load_payment_term_id = self.env['load.payment.term'].search([('type_freq', '=', 'fortnight')], limit=1)
                
            if not self.load_statuses or len(self.load_statuses) == 0:
                self.load_statuses = self.env['partner.load.status'].search([('name', 'in', ["Waiting For CLC approval", "CLC Approved", "In Accounting"])])
            if not self.exo_load_start_date:
                self.exo_load_start_date = datetime(2024, 7, 1, 0, 0, 0)
            
        elif self.internal_partner_type == 'shipper':
            self.search_by_warehouse = True
            self.group_by_warehouse = True
            self.apply_other_deductions = False
            self.create_by_automatic_load = True
            self.group_by_payment_term = True
            self.rounded_money = True
        
        
    @api.model
    def create(self, vals):
        _logger.info("____________ VALS")
        _logger.info(vals)
        if 'vat' in vals and vals['vat']:
            existing_partner = self.search([('vat', '=', vals['vat'])], limit=1)
            if existing_partner:
                raise ValidationError("El número de identificación (VAT) ya está registrado en otro contacto.")

            if vals.get('internal_partner_type', None) == 'transporter':
                to_insert_exo_transporters = self.get_exo_transporters(vals['vat'])

                if len(to_insert_exo_transporters) == 0:
                    raise ValidationError(f"No se encontraron transportistas con el número de identificación (RNC) {vals['vat']}")
                vals['partner_object_ids'] = to_insert_exo_transporters
            
        partner =  super(partner_inherit, self).create(vals)
        self.validate_and_edit(partner)
        return partner

    def write(self, vals):
        vals['pending_to_sign'] = True
        
        if vals.get('vat', None) or vals.get('internal_partner_type', None) == 'transporter':
            
            internal_partner_type = vals.get('internal_partner_type', None) or self.internal_partner_type
            
            to_insert_exo_transporters = self.get_exo_transporters(vals.get('vat', self.vat), [obj.name for obj in (self.partner_object_ids or [])])

            if internal_partner_type and len(to_insert_exo_transporters) == 0 and not self.partner_object_ids:
                raise ValidationError(f"No se encontraron transportistas con el número de identificación (RNC) {vals['vat']}")
            vals['partner_object_ids'] = to_insert_exo_transporters
            
        partner = super(partner_inherit, self).write(vals)
        self.validate_and_edit(self)
        
        return partner

    def get_exo_transporters(self, vat, existing_transporter_ids = []):
        exo_transporters = post_request_exo('exo/transportersByRnc', { "rnc": [vat] }, )
        result = exo_transporters.get('Result', [])
        to_insert = []
        for transporter in result:
            if transporter.get('_id', None) not in existing_transporter_ids:
                to_insert.append((0, 0, { 'name': transporter.get('_id', None), 'description': transporter.get('company_name', None) }))
        return to_insert
    
    def set_exo_transporters(self):
        self.ensure_one()
        to_insert = self.get_exo_transporters(self.vat, [obj.name for obj in (self.partner_object_ids or [])])
        
        has_data = self.partner_object_ids and len(self.partner_object_ids) > 0
            
        self.partner_object_ids = to_insert if to_insert else None

        if len(to_insert) == 0 and not has_data:
            raise ValidationError(f"No se encontraron transportistas con el número de identificación (RNC) {self.vat}")
        
        return  {'type': 'ir.actions.client', 'tag': 'reload'}
        
            
        
    def validate_and_edit(self, records):
        for partner in records:
            if partner.internal_partner_type == 'transporter':
                if not partner.company_id:
                    raise ValidationError("La compañía es requerida.")
                
                if partner.company_id.code != 'EXOB':
                    raise ValidationError("La compañía debe ser EXO BUSINESS CONSULTING SRL")
                
                required_statuses = ["Waiting For CLC approval", "CLC Approved", "In Accounting"]
            
                current_statuses = partner.load_statuses.mapped('name')
                
                missing_statuses = [status for status in required_statuses if status not in current_statuses]
                if missing_statuses:
                    raise ValidationError(
                        "Debe seleccionar todos los siguientes estados obligatorios: %s"
                        % ", ".join(missing_statuses)
                    )
                if not partner.exo_load_start_date:
                    raise ValidationError("Debe seleccionar una fecha inicial para cargar las facturas de EXO.")
                
                if not partner.create_by_automatic_load:
                    raise ValidationError(f"Debe seleccionar la opción 'Permite que a este cliente se le creen facturas internamente a media noche' para {partner.name} / {partner.id}.")
                
                
                if not partner.load_payment_term_id:
                    raise ValidationError("Debe seleccionar una Frecuencia de Facturación.")

    
    @api.depends('invoice_ids.payment_id')
    def _compute_last_payment(self):
        for partner in self:
            payments = partner.invoice_ids.mapped('payment_id').filtered(lambda p: p.state == 'posted')
            
            partner.last_payment_id = False
            if payments:
                last_payment = max(payments, key=lambda p: p.date)
                partner.last_payment_id = last_payment
        
    def add_additional_tax(self, current_env, tax_ids):
        self.ensure_one()
        # Para Cedulas > 2% seguro de Carga y 2% para impuestos sobre la renta
        # Para RNC > 2% seguro de Carga
        
        if (self['apply_other_deductions']):
            
            other_deductions_2_percent = current_env['account.tax'].sudo().search([('tax_code', '=', '2OR')], limit=1)
            if not other_deductions_2_percent:
                raise ValidationError("El impuesto (Otras Retenciones 2%) no fue encontrado, revise si existe un impuesto con el codigo 2OR")
            
            if other_deductions_2_percent.id not in tax_ids: 
                tax_ids.append(other_deductions_2_percent.id)
                
    def transform_rnc(self, rnc):
        return rnc.replace("-", "").replace('\t', '').replace(' ', '')
    
    def create_user_from_partner(self):
        user_group = self.env.ref("base.group_portal") or False
        users_res = self.env['res.users']
        documentNumber = self.transform_rnc(self['vat'])
        
        exists_login = users_res.sudo().search([('login', '=', documentNumber)], limit=1)
        if (exists_login):
            return exists_login[0]
            
        
        if (len(self.user_ids) > 0):
            return self.user_ids[0]

        if not self.user_id:
            if (not self['vat']):
                raise ValidationError(f"El usuario {self.name} no tiene configurado un RNC")
            login_info = {
                'name': self.name,
                'partner_id': self.id,
                'login': documentNumber,
                'password': os.getenv('USER_PASSWORD'),
                'groups_id': user_group,
                'tz': self._context.get('tz'),
            }
            _logger.info("________________ login info")
            user_id = users_res.create(login_info)
            return user_id
        
    
    def get_benefits_line_to_create_to_this_months(self, current_env = None):
        current_env = current_env if current_env else request.env
        self.ensure_one()
        
        benefits_line_to_create = []
        current_date = datetime.now()
        _logger.info("________________ ********** get get_benefits_line_to_create_to_this_months ******* _________________")
        _logger.info(self.id)
        _logger.info(datetime(current_date.year, current_date.month, 1))
        _logger.info(datetime.today())
        current_month_partner_lines = current_env['account.move.line'].sudo().search([
            ('move_id.state', '!=', 'cancel'),
            ('move_id.partner_id', '=', self.id),
            ('create_date', '>=',  datetime(current_date.year, current_date.month, 1)),
            ('create_date', '<=', datetime.today()),
        ])
        _logger.info("current_month_partner_lines")
        _logger.info(current_month_partner_lines)

        for p_benefit_discount in self['benefit_discount_ids']:
            for cicle in p_benefit_discount['benefit_discount_id']['benefit_discount_cicles_ids']:
                if (cicle.next_curt_date.day <= current_date.day):
                    _logger.info("p_benefit_discount")
                    _logger.info(p_benefit_discount)
                    _logger.info("cicle")
                    _logger.info(cicle)
                    current_month_benefits_cicle_lines = current_month_partner_lines.filtered(lambda ml: ml.benefit_discount_id.id == p_benefit_discount.benefit_discount_id.id and ml.benefit_discount_cicle_id.id == cicle.id)
                    _logger.info("current_month_benefits_cicle_lines")
                    _logger.info(current_month_benefits_cicle_lines)
                    if (not current_month_benefits_cicle_lines or len(current_month_benefits_cicle_lines) == 0):
                        _logger.info("not current_month_benefits_cicle_lines or len(current_month_benefits_cicle_lines) == 0")
                        benefits_line_to_create.append({'partner_id': self.id, 'p_benefit_discount': p_benefit_discount, 'cicle': cicle})
        _logger.info("****************** benefits_line_to_create -*  ****************** ")
        _logger.info(benefits_line_to_create)
        return benefits_line_to_create
    
    def get_unique_benefits_line_to_create_to_this_months(self, current_env = None):
        current_env = current_env if current_env else request.env
        self.ensure_one()
        
        current_date = datetime.now()
        current_month_partner_lines = current_env['unique.benefit.discount'].sudo().search([
            ('partner_id', '=', self.id),
            ('move_line_id', '=', False),
            ('create_date', '>=', datetime(current_date.year, 1, 1)),
            ('create_date', '<=', datetime.today()),
        ])
        _logger.info("****************** unique.benefit.discount -*  ****************** ")
        _logger.info(current_month_partner_lines)
        _logger.info(datetime(current_date.year, 1, 1))
        _logger.info(datetime.today())
        return current_month_partner_lines if current_month_partner_lines else []
