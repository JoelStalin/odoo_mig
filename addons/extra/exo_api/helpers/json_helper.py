import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

def get_value_from_json_property(property_subdived, json_load, depth = 1000, load = None, order = None, prop = None):
    order = json_load.get('order_num')  if type(json_load) is dict and json_load.get('order_num', False) else order
    if (depth <= 0):
        raise ValidationError("Validation Error: ha excedido la cantidad de ciclos permitido. Comuniquese con su administrador")
    
    if (type(json_load) is list):
        result_list = []
        for current_json in json_load:
            element = get_value_from_json_property(property_subdived, current_json, depth - 1, load, order, prop)
            result_list.append(element)
        return result_list
    
    elif (type(json_load) is dict):
        firstProperty = property_subdived[0]
        
        if (firstProperty not in json_load):
            _logger.info("_______________________________ JSON LOAD PROPIEDAD NO VALIDAD")
            _logger.info(json_load)
            _logger.info("_______________________________ CARGA __________________________")
            _logger.info(load)
            _logger.info(order)
            raise ValidationError(f"No se pudo encontrar la propiedad {load} / {order} / {prop} / {str(property_subdived)} en la data proporcionada" )
        
        if (len(property_subdived) == 1 ):
            return json_load[firstProperty]
        else: 
            return get_value_from_json_property(property_subdived[1:], json_load[firstProperty], depth - 1, load, order, prop)
        
    else:
        return json_load


def procesar_arreglo_recursivo(arr):
    resultado = []
    
    for elemento in arr:
        if isinstance(elemento, list):
            resultado.append(concatenar_subarreglo(elemento))
        else:
            resultado.append(elemento)
    
    return resultado

def concatenar_subarreglo(subarr):
    subresultado = ''
    for subelemento in subarr:
        if isinstance(subelemento, list):
            subresultado += concatenar_subarreglo(subelemento) + ' - '
        else:
            subresultado += str(subelemento) + ' - '
    return subresultado.rstrip(' - ')
