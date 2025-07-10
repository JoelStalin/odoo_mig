import os
import requests
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

# def request_sync(url, data):
#     headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache", "api-key": os.getenv('EXO_API_KEY')}
#     response = requests.post('https://8692-2001-1308-1cad-1600-f9d0-e292-685e-b78.ngrok-free.app' + url, json=data, headers=headers)
#     if response.status_code != 200:
#         _logger.info("No se pudo enviar la nueva cuenta contable a EXO")



def get_cookie(cookie = None):
    if cookie :
        return cookie
    
    data = { "email": str(os.getenv('EXO_USER')), "password": str(os.getenv('EXO_PASSWORD'))}
    endpoint_url = str(os.getenv('HOST_EXO')) + '/exo/authenticate/'
    response_authenticate = requests.post(url=endpoint_url, json=data)
    if response_authenticate.status_code != 200:
        raise ValidationError('La carga no pudo ser procesada debido a temas de authenticacion. \nCode: %s\nContent: %s' % (response_authenticate.status_code, response_authenticate.content))
    
    resp  = response_authenticate.json()
    cookie = resp['data']['cookie'][0]
    return cookie

def post_request_exo(endpoint, data):
    host_exo = os.getenv('HOST_EXO')
    cookie = get_cookie()
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache", "auth": cookie}
    url = f'{host_exo}/{endpoint}'
    _logger.info("_________ post_request_exo")
    _logger.info(url)
    _logger.info(cookie)
    _logger.info(data)
    response = requests.post(url, json=data, headers=headers)
    _logger.info(response)
    _logger.info(response.status_code)
    if response.status_code != 200:
        raise ValidationError('La carga no pudo ser procesada. 5. nCode: %s\nContent: %s' % (response.status_code, response.content))
    result = response.json()
    
    return result
