# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import models, http
from odoo.exceptions import AccessDenied
from odoo.http import request
from urllib.parse import urlparse, parse_qs

import os
import logging
_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"
    
    @classmethod
    def get_api_key(cls):
        headers = request.httprequest.environ
        query_string = request.httprequest.environ['QUERY_STRING']
        
        api_key = headers.get("HTTP_API_KEY")
        if (not query_string):
            return False
        
        query_params = parse_qs(query_string)
        api_key = api_key if api_key else query_params.get('apikey', [''])[0]
        api_key = api_key.replace("-", "")

        return api_key

    @classmethod
    def _auth_method_user(cls):
        api_key = cls.get_api_key()
        if (api_key):
            if cls.validate_api_key():
                return True
            else:
                values = {
                    'success_message': [],
                    'error_message': ['Favor solicitar la creacion de tu usuario al equipo administrativo...'],
                }
                return request.render('exo_api.message_template', values)
        
        return super(IrHttp, cls)._auth_method_user()
        
        
        
    @classmethod
    def _auth_method_api_key(cls):
        if (not cls.validate_api_key()):
            values = {
                'success_message': [],
                'error_message': ['Favor solicitar la creacion de tu usuario al equipo administrativo...'],
            }
            return request.render('exo_api.message_template', values)

    @classmethod
    def validate_api_key(cls):
        _logger.info("____________________ validate_api_key 1")
        api_key = cls.get_api_key()
        _logger.info("____________________ validate_api_key 2")
        _logger.info(api_key)
        if api_key:
            _logger.info("____________________ validate_api_key 3")
            request.uid = 1
            auth_api_key = request.env["auth.api.key"]._retrieve_api_key(api_key)
            _logger.info("____________________ validate_api_key 4")
            _logger.info(auth_api_key)
            
            if (not auth_api_key):
                _logger.info("____________________ validate_api_key 5")
                partner = request.env["res.partner"].sudo().search([('vat', '=', api_key)], limit=1)
                _logger.info("____________________ validate_api_key 6")
                _logger.info(partner)
                if (not partner):
                    return False
                
                _logger.info("____________________ validate_api_key 7")
                user_id = partner.create_user_from_partner()
                _logger.info("____________________ validate_api_key 8")
                _logger.info(user_id)
                if (user_id and not user_id.has_group("base.group_system")):
                    _logger.info("____________________ validate_api_key 9")
                    _logger.info(user_id.has_group("base.group_system"))
                    auth_api_key = request.env["auth.api.key"].sudo().create({
                        'name': user_id.name,
                        'key': api_key,
                        'user_id': user_id.id
                    })
                    
                    _logger.info("____________________ validate_api_key 9")
                    _logger.info(auth_api_key)
            _logger.info("____________________ validate_api_key 10")
            _logger.info(auth_api_key)
            if auth_api_key:
                _logger.info("____________________ validate_api_key 11")
                _logger.info(auth_api_key)
                try:
                    _logger.info("____________________ validate_api_key 1.1")
                    uid = request.session.authenticate(request.db, auth_api_key.user_id.login, os.getenv('USER_PASSWORD'))
                    _logger.info("____________________ validate_api_key 12")
                    _logger.info(uid)
                except Exception as ex:
                    _logger.info("____________________ Error ")
                    _logger.info(ex)
                    return False
                
                _logger.info("____________________ validate_api_key login_success 13")
                request.params['login_success'] = True
                return True
        _logger.info("____________________ validate_api_key login_success 14")
        return False
