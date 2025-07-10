from odoo import models, fields


class PartnerLoadStatus(models.Model):
    _name = "partner.load.status"
    _description = 'Estado a filtrar de una carga por cliente'

    name = fields.Char("Descripción del Status", required = True)
    key = fields.Char("Clave en EXO del Status", required = True)
    
    # Posibles Estados
    # Defining Load
    # Driver selection in progress
    # Driver Assigned
    # Expecting Approval
    # Approved
    # Driver Arrival
    # Loading Truck
    # Truck Loaded
    # Dispatched

    # Delivered
    # Waiting For TLC approval
    # TLC Approved
    # Waiting For CLC approval
    # CLC Approved
    # In Accounting
    # Finish Load
    # Denied Approval