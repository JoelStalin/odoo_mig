# from ...helpers.request_helper import request_sync
# from odoo import models, api

# class account_account_inherit(models.Model):
#     _inherit = "account.account"
    
#     def unlink(self):
#         res = super(account_account_inherit, self).unlink()
#         self.sync()
#         return res
    
#     def write(self, vals):
#         res = super(account_account_inherit, self).write(vals)
#         self.sync()
#         return res
    
#     @api.model
#     def create(self, vals):
#         res = super(account_account_inherit, self).create(vals)
#         self.sync()
#         return res

#     def sync(self):
#         records = self.sudo().search([])
#         data = []
#         for record in records:
#             data.append({
#                 'name': record['name'],
#                 'code': record['code'],
#                 'opening_debit': record['opening_debit'],
#                 'opening_credit': record['opening_credit'],
#                 'opening_balance': record['opening_balance']
#             })
#         request_sync('/account_accounts', data)