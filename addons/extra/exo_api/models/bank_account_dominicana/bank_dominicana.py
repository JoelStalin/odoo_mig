class BankDominicana(models.Model):
    _name = 'bank.dominicana'
    _description = 'Catálogo de Bancos en RD'

    name = fields.Char(string='Nombre del Banco', required=True)
    code = fields.Char(string='Código del Banco (3 caracteres)', required=True, size=3)
    swift = fields.Char(string='Código SWIFT', required=True)

    _sql_constraints = [
        ('bank_code_unique', 'UNIQUE(code)', 'El código del banco debe ser único.'),
    ]
