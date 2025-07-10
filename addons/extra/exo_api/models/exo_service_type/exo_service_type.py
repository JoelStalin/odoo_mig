from odoo import models, fields

class exo_service_type(models.Model):
    _name = "exo.service.type"
    _description = 'Tipos de Servicios de EXO'

    name = fields.Char(string = 'Nombre del Servicio')
    