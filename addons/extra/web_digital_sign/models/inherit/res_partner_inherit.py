from odoo import api, fields, models
from datetime import datetime
def _value_to_text(value):
    """
    Función de ayuda para convertir un valor (many2one, many2many, etc.)
    a un texto legible que se pueda mostrar en el 'review'.
    """
    if not value:
        return ""

    # Si es un recordset many2one
    if hasattr(value, 'name') and isinstance(value.id, int):
        return value.name or ""

    # Si es un recordset de tipo many2many o one2many
    if hasattr(value, '__len__') and hasattr(value, 'mapped'):
        # Podemos mapear por 'name', 'display_name' o el campo que se desee
        names = value.mapped('name')
        return ", ".join(names)

    # Para otros tipos (char, float, int, etc.)
    return str(value)



class PartnerInherit(models.Model):
    _inherit = "res.partner"

    digital_signature = fields.Binary(string="Firma y Consentimiento", tracking=True)
    pending_to_sign = fields.Boolean("Pendiente de Firmar", required=True, tracking=True)
    digital_sign_date = fields.Datetime('Fecha de la Firma', tracking=True)

    change_text = fields.Text(
        string="Revisión de Cambios",
        compute="_compute_change_text",   # Campo computado
        store=False                       # Probablemente no quieras guardarlo en BD de manera permanente
    )

        
    @api.onchange('company_id', 'analytic_tag_ids', 'exo_load_configurations', 'exo_load_start_date', 
                  'benefit_discount_ids', 'vat', 'load_statuses', 'search_by_warehouse', 
                  'create_by_automatic_load', 'group_by_payment_term', 'group_by_warehouse', 
                  'rounded_money', 'load_payment_term_id',
                  'insurance_percent', 'apply_other_deductions', 
                  'document_type', 'internal_partner_type')
    def _onchange_any_partner_field(self):
        self.pending_to_sign = False
        self.digital_signature = False
        self.digital_sign_date = datetime.now()
        
    @api.depends(
        'company_id', 'analytic_tag_ids', 'exo_load_configurations', 'exo_load_start_date',
        'benefit_discount_ids', 'vat', 'load_statuses', 'search_by_warehouse',
        'create_by_automatic_load', 'group_by_payment_term', 'group_by_warehouse',
        'rounded_money', 'load_payment_term_id',
        'insurance_percent', 'apply_other_deductions',
        'document_type', 'internal_partner_type'
    )
    def _compute_change_text(self):
        """
        Muestra en 'change_text' un texto que compara los valores guardados en BD (viejos)
        vs. los valores actuales en memoria (nuevos). Útil como 'review' antes de guardar.

        - Si el registro aún no existe en la BD (no tiene 'id'), consideramos 'valores viejos' = vacío.
        - Si ya existe, hacemos un browse/ read del partner para ver sus valores reales en BD.
        """
        # Lista de campos que queremos comparar
        fields_to_compare = [
            'company_id', 'analytic_tag_ids', 'exo_load_configurations', 'exo_load_start_date',
            'benefit_discount_ids', 'vat', 'load_statuses', 'search_by_warehouse',
            'create_by_automatic_load', 'group_by_payment_term', 'group_by_warehouse',
            'rounded_money', 'load_payment_term_id',
            'insurance_percent', 'apply_other_deductions',
            'document_type', 'internal_partner_type'
        ]

        for record in self:
            record.change_text = ""
            if record.company_id:
                record.change_text += f"\Compañia: ****{record.company_id.name}****"
            
            if record.load_statuses and len(record.load_statuses) > 0:
                record.change_text += f"\nEstados a filtrar en EXO: **** {','.join([x.name for x in record.load_statuses])} ****"
            
            if record.vat:
                record.change_text += f"\nNo. de Documento: ****{record.vat}****"
                
            if record.create_by_automatic_load:
                record.change_text += f"\nPermite que a este cliente se le creen facturas internamente a media noche: ****{record.create_by_automatic_load}****"

            if record.group_by_payment_term:
                record.change_text += f"\nPermite que la factura se pueda agrupar por Frecuencia de Facturación: ****{record.group_by_payment_term}****"


            if record.load_payment_term_id:
                record.change_text += f"\nFrecuencia de Facturación: ****{record.load_payment_term_id.name}****"

            if record.insurance_percent:
                record.change_text += f"\nSeguro de Carga: ****{record.insurance_percent}****"
            
            if record.apply_other_deductions:
                record.change_text += f"\nAplicar Impuesto (Otras Retenciones 2%): ****{record.apply_other_deductions}****"

            if record.search_by_warehouse:
                record.change_text += f"\nPermite la busqueda por warehouse a este cliente: ****{record.search_by_warehouse}****"
                
            if record.group_by_warehouse:
                record.change_text += f"\nPermite que la factura se pueda agrupar por warehouse: ****{record.group_by_warehouse}****"
                
            if record.document_type:
                record.change_text += f"\nTipo de Documento: ****{record.document_type}****"
                
            if record.analytic_tag_ids and len(record.analytic_tag_ids) > 0:
                record.change_text += f"\nEtiquetas Analíticas: ****{','.join([x.name for x in record.analytic_tag_ids])}****"
            
            
            if record.benefit_discount_ids and len(record.benefit_discount_ids) > 0:
                record.change_text += f"\nBeneficios y descuentos Mensuales de clientes: ****{','.join([x.name for x in record.benefit_discount_ids])}****"
            
            if record.exo_load_start_date:
                record.change_text += f"\nFecha Inicial de la Carga{str(record.exo_load_start_date.strftime('%Y%m%d'))}"
            