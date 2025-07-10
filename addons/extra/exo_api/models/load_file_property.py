from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

class load_file_property(models.Model):
    _name = 'load.file.property'
    _description = 'Propiedad'
    
    name = fields.Char("Etiqueta", required=True)
    
    template_id = fields.Many2one('template.load.file.property', string='Plantilla')
    key = fields.Char("Campo en el JSON", required=True, help="Nombre ubicado en el JSON proveniente de la carga de EXO, puedes acceder a las propiedades anidadas del json usando punto independientemente de que sea un arreglo ejemplo {'orders': [{'num': 23}] } para defenir este key seria: orders.num entonces el sistema se encargara de obtener el de cada uno de los numeros de ordenes. ")
    type = fields.Selection([('normal', 'Normal'), ('compute', 'Computado')], 'Tipo', default='normal', required=True, help="Indica si el tipo es un campo existente en el json de la carga o si sera creado a partir de los campos de los datos por ejemplo: campo (createdAt) puedes crear un campo computado que te obtenga el mes (datetime.strptime(data_to_export['createdAt']['value'], '%Y/%m/%d %H:%M').month)")
    calculation_mode = fields.Selection([('precombination', 'Pre Combination'), ('postcombination', 'Post Combination')], 'Modo de Calculacion', default='precombination', required=True, help="Indica si la operacion se realizara antes o despues de realizar todas las combinaciones.")
    show = fields.Boolean("Ver en Archivo", required=True, default=True, help="Si el campo se mostrara en el PDF o EXCEL a descargar. Ejemplo tengo un campo computado Mes que fue creado a partir de la fecha. El campo Fecha no me interesa que se muestre pero si el campo mes. Ambos cambos deben ser creados pero debe especificar si quieres que se muestren ambos o solo uno de ellos")
    order = fields.Integer("Secuencia", help="Secuencia o Orden con el cual las columnas se mostrarán")
    value = fields.Text(string="Formula", attrs={'invisible': [('type', '!=', 'normal')], 'required': [('type', '=', 'normal')]},   help='Formula o codigo python a ejecutar: El codigo provee una variable data_to_export donde se encuentra el json creado con las propiedades menor a la secuencia actual. Ejemplo en el json existe una propiedad llamada currencyExchange.atTheTimeOfAssigning la cual te obtiene la moneda de cambio actual de esa carga. Este campo se encuentra en la secuencia 1 y luego creaste una propiedad computada atTheTimeOfAssigningTax la cual genera el currence mas 18 porc de descuento (ubicada en la secuencia 2). Entonces quieres crear una tercera propiedad computada el cual use esas dos propiedades:     round(data_to_export["currencyExchange.atTheTimeOfAssigning"]["value"] / data_to_export["atTheTimeOfAssigningTax"]["value"], 2). Nota que el uso de data_to_export y el uso de ["value"] al final de cada propiedad')
    is_active = fields.Boolean('Activo?', default=True, required=True)
    duplicate_with_sub_list = fields.Boolean("Duplicar con sublista",  default=True, help="Si necesitas mostrar los campos de ordenes o cualquier otra sublista, entonces en el excel no mostrara dos o mas veces este valor")
