import uuid
import json
from odoo.http import request
from odoo import fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError

import threading

import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    def send_message_channel(self, message_subject, message_body):
        try:
            _logger.info("7777777 step 1")
            odoobot_id = self.env['ir.model.data'].sudo()._xmlid_to_res_id("base.partner_root")
            _logger.info("7777777 step 2")
            channel = self.env['mail.channel'].sudo().search([('name', '=', 'Cambios en Facturas')])
            _logger.info("7777777 step 3")
            if not channel:
                _logger.info("7777777 step 4")
                channel = self.env['mail.channel'].create({
                    'name': 'Cambios en Facturas',
                    'channel_partner_ids': [(4, user.sudo().partner_id.id) for user in self.sudo()]
                })
                _logger.info("7777777 step 4.1")
            else:
                _logger.info("7777777 step 4.2")
                channel.sudo().write({
                    'channel_partner_ids': [(4, user.sudo().partner_id.id) for user in self.sudo()]
                })
                _logger.info("7777777 step 4.3")
            
            _logger.info("7777777 step 4.4")
            channel.sudo()._subscribe_users_automatically()
                
            _logger.info("7777777 step 5")
            message = f"<br/><b style='color: red'>{message_subject}</b>.<br/><div>{message_body}</div>"
            _logger.info("7777777 step 6")
            channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype_xmlid="mail.mt_comment")
            _logger.info("7777777 step 7")
            
        except Exception as ex:
            _logger.info("No se ha logrado enviar el mensaje deseado al canal correspondiente. Datos del mensaje: ")
            _logger.info(ex)
            _logger.info(message_subject)
            _logger.info(message_body)
  