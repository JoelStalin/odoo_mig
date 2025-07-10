from odoo import models, fields, api, _


BANK_DATA = {
    'BRR': {'swift': 'BRRDDOSDXXX', 'name': 'Banco de Reservas (BRR)'},
    'BPD': {'swift': 'BPDODOSXXXX', 'name': 'Banco Popular Dominicano (BPD)'},
    'BHD': {'swift': 'BCBHDOSDXXX', 'name': 'BANCO MULTIPLE BHD (BHD)'},
    'SCR': {'swift': 'SCRZDOSDXXX', 'name': 'Banco Santa Cruz (SCR)'},
    'SCO': {'swift': 'NOSCDOSDXXX', 'name': 'Banco ScotiaBank (SCO)'},
    'PRM': {'swift': 'PRHRDOSDXXX', 'name': 'Promerica (PRM)'},
    'BAN': {'swift': 'BANSDOSDXXX', 'name': 'Banco Ademi (BAN)'},
    'CAR': {'swift': 'STGODOSDXXX', 'name': 'Banco Caribe (CAR)'},
    'BDI': {'swift': 'BBDIDOSDXXX', 'name': 'Banco BDI (BDI)'},
    'BLH': {'swift': 'BLDHDOSDXXX', 'name': 'Banco López de Haro (BLH)'},
    'CIT': {'swift': 'CITIDOSDXXX', 'name': 'CitiBank (CIT)'},
    'VIM': {'swift': 'VIMEDOSDXXX', 'name': 'Banco Vimenca (VIM)'},
    'ADE': {'swift': 'AHCMDOSDXXX', 'name': 'Banco Adopem (ADE)'},
    'LAF': {'swift': 'BCCEDOSDXXX', 'name': 'Banco Lafise (LAF)'},
    'JMM': {'swift': 'AHRIDOS2XXX', 'name': 'Banco JMMB (JMM)'},
    'QIK': {'swift': 'QDDMDOSDXXX', 'name': 'Banco Qik (QIK)'},
    'BAG': {'swift': 'BAGRDOSAXXX', 'name': 'Banco Agrícola (BAG)'},
    'ACF': {'swift': 'ACFEDOSCXXX', 'name': 'Banco ACF (ACF)'},
    'BEL': {'swift': 'BELNDOSDXXX', 'name': 'Banco BellBank (BEL)'},
    'CFC': {'swift': 'AHCCDOS2XXX', 'name': 'Confisa (CFC)'},
    'CFS': {'swift': 'AHCODOSMXXX', 'name': 'Confisa Servicios (CFS)'},
    'FIH': {'swift': 'AHCGDOS3XXX', 'name': 'Fihellbank (FIH)'},
    'GRU': {'swift': 'BACGDOS1XXX', 'name': 'Grupo Financiero (GRU)'},
}


class BankAccountDominicana(models.Model):
    _name = 'bank.account.dominicana'
    _description = 'Cuenta Bancaria Dominicana'
    _rec_name = 'account_number'
    _order = 'partner_id, account_number'

    partner_id = fields.Many2one('res.partner', string='Beneficiario', required=True)
    account_number = fields.Char(string='Número de Cuenta', required=True)
    acc_holder_name = fields.Char(string='Titular / Alias', required=True)
    active = fields.Boolean(string="Activo", default=True)

    account_type = fields.Selection(
        selection=[
            ('CA', 'Cuenta de Ahorro'),
            ('CC', 'Cuenta Corriente'),
            ('PR', 'Préstamo'),
            ('TJ', 'Tarjeta de Crédito')
        ],
        string="Tipo de Producto", required=True,
    )

    transfer_type = fields.Selection(
        selection=[
            ('1', 'Cuentas de Tercero en el BHD León'),
            ('2', 'Tarjetas terceros en BHD León'),
            ('3', 'Préstamos terceros en BHD León'),
            ('4', 'ACH'),
            ('5', 'Pago al Instante')
        ],
        default='5',
        string="Tipo de Transacción",
        help="Seleccione el tipo de transacción: Cuentas de Tercero en el BHD León (1)",
    )
    bank_code = fields.Char(string='Código de Banco', required=True)
    swift_code = fields.Char(string='Código SWIFT', required=True)
    bank_name = fields.Char(string='Nombre del Banco')

    document_type = fields.Char(string='Tipo de Documento', compute='_compute_document_type', store=True)
    document_number = fields.Char(string='Documento', related='partner_id.vat', store=True)

    _sql_constraints = [
        (
            'unique_account_per_partner',
            'UNIQUE(partner_id, account_number)',
            'El número de cuenta ya está registrado para este partner.'
        ),
    ]

    @api.depends('partner_id')
    def _compute_document_type(self):
        for record in self:
            if record.partner_id and record.partner_id.vat:
                vat_len = len(record.partner_id.vat)
                if vat_len == 9:
                    record.document_type = 'R'
                elif vat_len == 11:
                    record.document_type = 'C'
                else:
                    record.document_type = 'P'
            else:
                record.document_type = 'N'

    @api.onchange('bank_code')
    def _onchange_bank_code(self):
        if self.bank_code:
            bank_info = BANK_DATA.get(self.bank_code)
            if bank_info:
                swift = bank_info['swift']
                if len(swift) < 11:
                    swift = swift.ljust(11, 'X')
                self.swift_code = swift
                self.bank_name = bank_info['name']
            else:
                self.swift_code = ''
                self.bank_name = ''

    @api.onchange('bank_code', 'partner_id')
    def _onchange_bank_code_or_partner_id(self):
        """
        Al cambiar el banco o el partner:
        1️⃣ Se llena automáticamente swift_code y bank_name.
        2️⃣ Si el banco NO es BHD, acc_holder_name toma el nombre del partner.
        3️⃣ Si es BHD, acc_holder_name queda vacío.
        """
        self._onchange_bank_code()  # Completa swift_code y bank_name

        if self.bank_code and self.partner_id:
            if self.bank_code != 'BHD':
                self.acc_holder_name = self.partner_id.name
            else:
                self.acc_holder_name = ''
        else:
            self.acc_holder_name = ''

    def action_actualizar_acc_holder_name(self):
        """
        Botón de acción para actualizar el campo acc_holder_name en todos los registros,
        según la lógica de negocio: si bank_code ≠ 'BHD', acc_holder_name = partner_id.name.
        """
        cuentas = self.env['bank.account.dominicana'].search([])
        for cuenta in cuentas:
            if cuenta.bank_code and cuenta.partner_id:
                if cuenta.bank_code != 'BHD':
                    cuenta.acc_holder_name = cuenta.partner_id.name
                elif cuenta.bank_code == 'BHD':
                    cuenta.transfer_type = '1'
                    cuenta.acc_holder_name = cuenta.acc_holder_name
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Actualización Completa'),
                'message': _('Se actualizaron los Titulares/Alias de las cuentas correctamente.'),
                'type': 'success',
                'sticky': False,
            }
        }
