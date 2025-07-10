from odoo import http
import json
from odoo.http import Response

def set_http_response(status):
        headers = http.request.httprequest.headers
        args = http.request.httprequest.args
        # data = http.request.jsonrequest
        http.Response.status = status

def handler_error(message, status, codeError):
        set_http_response(status)
        return {'error' : message, "status_response": status, 'coreError': codeError}

def response_success(response, status = '200 OK'):
        set_http_response(status)
        return {"data": response, "status_response": status}

def http_handler_error(message, status, http_status = "500 INTERNAL SERVER ERROR"):
        set_http_response(http_status)
        return Response(json.dumps({"jsonrpc": "2.0", "id": None,  "result": {"error": {"message": message, "status_response": http_status}}}), content_type='application/json;charset=utf-8',status=status)

def http_response_success(data, status = 200, http_status = "200 OK"):
        set_http_response(http_status)
        return Response(json.dumps({"jsonrpc": "2.0", "id": None, "result": {"data": data, "status_response": http_status}}), content_type='application/json;charset=utf-8',status=status)