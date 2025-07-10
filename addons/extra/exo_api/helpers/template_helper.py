import os
import json
from odoo.tools import file_open
from datetime import timedelta, timedelta, datetime

from odoo.exceptions import ValidationError
from .json_helper import get_value_from_json_property, procesar_arreglo_recursivo
import logging
_logger = logging.getLogger(__name__)

def get_data_to_export(json_obj, headers = []):
    headers = sorted(headers, key=lambda x: x['order'])
    list_obj = []
    if type(json_obj) is not list:
        list_obj.append(json_obj)
    else:
        list_obj = json_obj
    
    final_result = []
    for obj in list_obj:
        data_to_export = {}
        for property in list(filter(lambda x: x['type'] == 'normal', headers)):
            property_subdived = property['key'].split('.')
            
            data = get_value_from_json_property(property_subdived, obj, 1000, obj.get('loadNumber', ''), '', str(property_subdived))
            if isinstance(data, list):
                data = procesar_arreglo_recursivo(data)
            data_to_export[property['key']] = {"value": data, "show": property['show'], "name": property['name'],  "duplicate_with_sub_list": property['duplicate_with_sub_list'], "order": property['order']}
        for compute_property in list(filter(lambda x: x['type'] == 'compute', headers)):
            try:
                
                key_value = eval(compute_property['value']) if compute_property['calculation_mode'] == 'precombination' else f"eval(\"{compute_property['value']}\")"
                
                data_to_export[compute_property['key']] = {"value": key_value , "show": compute_property['show'], "name": compute_property['name'], "duplicate_with_sub_list": compute_property['duplicate_with_sub_list'], "order": compute_property['order']}
            except Exception as e:
                _logger.info(data_to_export)
                raise ValidationError(f"Error evaluando la propiedad computada ({compute_property['key']}) con el valor: ({compute_property['value']}). Error: {e}")
        
       
        new_property = {}

        for k in data_to_export:
            new_property[k] = data_to_export[k]



        final_result.append(new_property)
    
    
    return final_result 
def get_data_from_json(header = [], path = 'exo_api/static/load_template.json'):
    with file_open(path, "rb") as f:
        json_obj = json.load(f)
        result = get_data_to_export(json_obj, header)
        
        return result
 

def generate_combinations(obj):
    keys = list(obj.keys())
    keys = sorted(keys, key=lambda k: obj[k]['order'])
    
    values = [obj[key]['value'] if isinstance(obj[key]['value'], list) else [obj[key]['value']] for key in keys]
    
    # Encuentra la longitud máxima de los valores
    max_length = max(len(value) for value in values)
    # Rellena los valores que tienen menos elementos
    for i in range(len(keys)):
        current_value = values[i][-1] if values[i] and len(values[i]) > 0 else ''
        if (obj[keys[i]]['duplicate_with_sub_list']):
            values[i] += [current_value] * (max_length - len(values[i]))
        else:
            values[i] += [None] * (max_length - len(values[i]))

    # Genera las combinaciones
    result = []
    for j in range(max_length):
        combination = [values[i][j] for i in range(len(keys))]
        result.append(combination)

    result = pos_combination_eval(result, obj, keys)
    result = get_only_show(result, obj, keys)
    return result

def get_only_show(result, obj, keys):
    keys = keys
    for index in range(len(keys)):
        key = keys[index]
        for sub_array in result:
            if (not obj[key]['show']):
                sub_array[index] = 'N/A'
    new_array = []
    for s_a in result:
        n_sa = []
        for v in s_a:
            if (v != 'N/A'):
                n_sa.append(v)
        new_array.append(n_sa)
    return new_array
    
    
def pos_combination_eval(result, obj, keys):
    for data_to_export in result:
        for i in range(len(data_to_export)):
            
            if (isinstance(data_to_export[i], str) and 'eval' in data_to_export[i]):
                for k in range(len(keys)):
                    if keys[k] in data_to_export[i]:
                        data_to_export[i] = data_to_export[i].replace(f'"{keys[k]}"', str(k))
                data_to_export[i] = eval(data_to_export[i])

    return result

def add_subtotals(result):
    # Agregar la fila de total si todos los valores en la columna son numéricos
    if (len(result) > 0):
        total_row = []
    
        for row_index in range(len(result[0])):
            total = 0
            for col_index in range(len(result)):
                value = result[col_index][row_index]
                if isinstance(value, (int, float)):
                    total += value

            total = '' if total == 0 else total
            total_row.append(total)
    
        result.append(total_row)
