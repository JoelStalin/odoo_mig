from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BenefitDiscountCicle(models.Model):
    _name = "benefit.discount.cicle"
    _description = 'Ciclo del Descuento'

    name = fields.Char("Nombre del Ciclo", required=True)
    next_curt_date = fields.Date("Siguiente fecha de corte", required=True)
    
    @api.constrains('next_curt_date')
    def _check_next_curt_date(self):
        for record in self:
            if record.next_curt_date:
                day = record.next_curt_date.day
                if day < 1 or day > 28:
                    raise ValidationError("La fecha de corte debe estar entre el 1 y el 28 del mes.")