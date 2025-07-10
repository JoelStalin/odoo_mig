# -*- coding: utf-8 -*-
from odoo import models, fields

# Añadimos ondelete vacío a Char para evitar el AttributeError
if not hasattr(fields.Char, 'ondelete'):
    fields.Char.ondelete = {}
