from odoo import models, fields, api

class ResBank(models.Model):
    _inherit = 'res.partner.bank'

    product_type = fields.Selection(
        selection=[('CA', 'Cuenta de Ahorro'), ('CC', 'Cuenta Corriente'), ('PR', 'Prestamo'), ('TJ', 'Tarjeta Credito')],
        string="Tipo de Producto",
        help="Seleccione el tipo de transacción: Cuenta de Ahorro (CA) o Cuenta Corriente (CC)."
    )
    
    
    bank_code = fields.Char(string="Código Banco")

    transaction_type = fields.Selection(selection=[('1', 'Cuentas de Tercero en el BHD Leon'), ('2', 'Tarjetas terceros en BHD LEON'), ('3', 'Prestamos terceros en BHD Leon'), ('4', 'ACH'), ('5', 'Pago al instante')], string="Tipo de Transacción")
    