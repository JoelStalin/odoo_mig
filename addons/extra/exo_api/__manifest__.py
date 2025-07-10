{
    "name": "API",
    "version": "17.0.1.0.0",
    "sequence": 2,
    "author": "Emy Saul Soto. <emysaul@hotmail.es>",
    "summary": "Este modulo agrega la posibilidad de crear factura a traves de un API",
    "depends": ["sale_management", "account", "stock", "hr_payroll", "contacts", "account_reports", "report_xlsx", "account_batch_payment"],
    'installable': True,
    'application': True,
    'data': [
        'security/exo_api_group.xml',
        # Paginas Webs Publicas
        'web_site_views/account_line_load_website_view.xml',
        
        # Otros XMLS
        'views/templates/message_template.xml',
        'views/inherit/account/account_load.xml',
        'views/inherit/account/account_invoice_portal.xml',
        'views/inherit/account/account_invoice_tax_totals.xml',
        'views/inherit/account/tax_groups_totals.xml',
        
        'security/load_security/ir.model.access.csv',

        'views/inherit/partner/partner.xml',
        'security/res_partner_tag/ir.model.access.csv',

        'views/hr_payslip_line/hr_payslip_line_menu.xml',
        'views/hr_payslip_line/hr_payslip_line.xml',

        'views/inherit/account_payment/account_payment.xml',
        'views/inherit/account_move/account_move.xml',
        'views/inherit/account_move/account_fiscal_position.xml',
        'security/res_partner_object/ir.model.access.csv',
        # 'views/inherit/account_move/account_move_line.xml',

        'views/inherit/hr_payslip/hr_payslip.xml',
        'views/inherit/hr_payslip/hr_payslip_xlsx.xml',

        'views/inherit/hr_salary_rule/hr_salary_rule.xml',

        'views/account_account/account_account_menu.xml',

        'views/exo_partner_load_configuration/exo_partner_load_configuration_menu.xml',
        'views/exo_partner_load_configuration/exo_partner_load_configuration.xml',
        'security/exo_partner_load_configuration/ir.model.access.csv',
        
        'security/exo_load_configuration_field/ir.model.access.csv',

        'views/account_line_load/account_line_load_menu.xml',
        'views/account_line_load/account_line_load.xml',
        'security/account_line_load/ir.model.access.csv',
        
        'views/account_line_deleted_load/account_line_deleted_load_menu.xml',
        'views/account_line_deleted_load/account_line_deleted_load.xml',
        'security/account_line_deleted_load/ir.model.access.csv',


        'views/drives_client/drives_client_menu.xml',
        'views/drives_client/drives_client.xml',
        'security/drives_client/ir.model.access.csv',
        
        
        'views/res_partner_object/res_partner_object.xml',
        'views/res_partner_object/res_partner_object_menu.xml',
        'security/res_partner_object/ir.model.access.csv',
        
        
        'views/benefits_and_discounts/benefits_and_discounts.xml',
        'views/benefits_and_discounts/unique_benefits_and_discount.xml',
        'views/benefits_and_discounts/unique_benefits_and_discount_wizard.xml',
        'views/benefits_and_discounts/unique_benefits_and_discount_scheduled.xml',
        'views/benefits_and_discounts/unique_benefits_and_discount_transaction.xml',
        'views/benefits_and_discounts/discount_carrier.xml',
        'views/benefits_and_discounts/discount_load_view.xml',
        'views/benefits_and_discounts/discount_parameters.xml',
        'views/benefits_and_discounts/benefits_and_discounts_menu.xml',
        'security/benefits_and_discounts/ir.model.access.csv',
        
        
        'views/partner_load_status/partner_load_status.xml',
        'views/partner_load_status/partner_load_status_menu.xml',
        'security/partner_load_status/ir.model.access.csv',
        
        'views/account_load_error/account_load_error.xml',
        'views/account_load_error/account_load_error_menu.xml',
        'security/account_load_error/ir.model.access.csv',
        
        'views/load_payment_term/load_payment_term.xml',
        'views/load_payment_term/load_payment_term_menu.xml',
        'security/load_payment_term/ir.model.access.csv',
        
        
        'views/load_file_property/load_file_property.xml',
        'views/load_file_property/template_load_file_property.xml',
        'views/load_file_property/template_load_file_property_menu.xml',
        'security/load_file_property/ir.model.access.csv',
        
        'views/exo_odoo_conciliation/exo_odoo_conciliation.xml',
        'security/exo_odoo_conciliation/ir.model.access.csv',
        
        'security/tax_additional_product/ir.model.access.csv',
        'security/account_analytic_warehouse/ir.model.access.csv',
        
        'views/inherit/account_move/account_tax.xml',
        'views/inherit/res_partner_bank/res_partner_bank.xml',
        

        'views/inherit/res_company/res_company.xml',        


        'views/inherit/account_analytic_account/account_analytic_account.xml',
        'views/inherit/account_batch_payment/account_batch_payment_views.xml',

        'views/excel_transaction_lot/excel_transaction_bhd_report.xml',
        'views/excel_transaction_lot/excel_transaction_others_report.xml',
        'views/invoice_fully_loaded_wizard/invoice_fully_loaded_wizard.xml',
        'security/invoice_fully_loaded_wizard/ir.model.access.csv',
        'views/bank_account_dominicana/bank_account_dominicana.xml',
        'security/bank_account_dominicana/bank_account_dominicana.xml',
        'security/bank_account_dominicana/ir.model.access.csv',
        
    ],
    "license": "LGPL-3",
}
