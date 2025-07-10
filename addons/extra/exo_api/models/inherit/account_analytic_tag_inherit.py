# from ...helpers.request_helper import request_sync
# from odoo import models, api

# class account_analytic_tag_inherit(models.Model):
#     _inherit = "account.analytic.tag"
    
#     def unlink(self):
#         res = super(account_analytic_tag_inherit, self).unlink()
#         self.sync()
#         return res
    
#     def write(self, vals):
#         res = super(account_analytic_tag_inherit, self).write(vals)
#         self.sync()
#         return res
    
#     @api.model
#     def create(self, vals):
#         res = super(account_analytic_tag_inherit, self).create(vals)
#         self.sync()
#         return res


#     def sync(self):
#         records = self.sudo().search([])
#         data = []
#         for record in records:
#             data.append({
#                 'name': record['name']
#             })
#         request_sync('/account_analytic_tags', data)