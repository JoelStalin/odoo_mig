from odoo import models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class InvoiceFullyLoadedWizard(models.TransientModel):
    _name = 'invoice.fully.loaded.wizard'
    _description = 'Wizard para generar templates de facturas cargadas'

    def execute_generate_templates(self):
        """
        Llama a los métodos ya definidos en el modelo account.load para generar las plantillas.
        Cierra las sesiones de otros usuarios antes de continuar.
        """
        env = self.env
        uid = env.uid

        # Buscar sesiones activas de otros usuarios (últimos 5 minutos)
        # Session = env['ir.sessions'].sudo()
        # active_sessions = Session.search([
        #     ('uid', '!=', uid),
        #     ('session_login', '!=', False),
        # ])

        # if active_sessions:
        #     # Cerrar sesiones de otros usuarios
        #     active_sessions.unlink()

        # Ejecutar procesos
        current_date_less_this_hours = 1300
        current_date_plus_this_hours = 144
        model = env['account.load']
        record = self
        records = self

        # Sincronización de facturas automáticas
        model.sudo().with_context(lang="es_DO", tz='America/Santo_Domingo')._sync_automatic_invoice(
            env, model, record, records, current_date_less_this_hours, current_date_plus_this_hours
        )

        # Adjuntar templates
        model.sudo().with_context(lang="es_DO", tz='America/Santo_Domingo').attach_template_to_invoice_fully_loaded(env)

        return {'type': 'ir.actions.client', 'tag': 'reload'}
