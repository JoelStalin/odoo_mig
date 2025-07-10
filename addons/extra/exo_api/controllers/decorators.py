from functools import wraps
from odoo.http import request
from odoo.addons.exo_api.controllers.response import response_success

def redirect_safe(url=None):
    """
    Decorador para funciones que deben redirigir de forma segura.
    Si se llama desde navegador, hace redirección.
    Si se llama desde API (accept: application/json), responde JSON.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            final_url = url or result  # usa URL fija o la que retorne la función
            if request.httprequest.accept_mimetypes.best == 'application/json':
                return response_success({'redirect': final_url})
            return request.redirect(final_url)
        return wrapper
    return decorator
