# -*- coding: utf-8 -*-
#----------------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# ayuda - Videos de ayuda y tutoriales para pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# contribuci?n de jurrabi
#----------------------------------------------------------------------
import os
from core import config
from core import logger
from core.item import Item
from platformcode import guitools

__channel__ = "test"

list_controls= [{'id': "nameControl1",
                      'type': "bool",                       # bool, text, list, label 
                      'label': "Control 1: tipo RadioButton",
                      'default': True,
                      'enabled': True,
                      'visible': True,
                      'lvalues':"",                         # only for type = list
                    },
                    {'id': "nameCóntrol2",
                      'type': "text",                       # bool, text, list, label 
                      'label': "Control 2: tipo Cuadro de texto",
                      'default': "Valor por defectó",
                      'enabled': True,
                      'visible': True,
                      'lvalues':"",                         # only for type = list
                    },
                    {'id': "nameControl3",
                      'type': "label",                       # bool, text, list, label 
                      'label': "Control 3: tipo Etiqueta",
                      'default': '',               # En este caso: valor opcional que representa el color del texto
                      'enabled': True,
                      'visible': True,
                      'lvalues':"",                         # only for type = list
                    },
                    {'id': "nameControl4",
                      'type': "list",                       # bool, text, list, label 
                      'label': "Control 4: tipo Lista",
                      'default': "item1",
                      'enabled': True,
                      'visible': True,
                      'lvalues':["item1", "item2", "item3", "item4"],                         # only for type = list
                    }]
                    
#dict_values={"nameControl1": False, "nameControl2": "Esto es un ejemplo"}
def isGeneric():
    return True

def mainlist(item):
    logger.info("[test.py] mainlist")
    itemlist = []

    itemlist.append( Item(channel=__channel__, action="settingCanal", title="[COLOR 0xFFEB7600][B]Configuración[/B][/COLOR]"))
    itemlist.append( Item(channel=__channel__, action="dialogBox", title="[COLOR 0xFFEB7600][B]Cuadro de dialogo[/B][/COLOR]"))
    itemlist.append( Item(channel=__channel__, action="get_setting", title="[COLOR 0xFFEB7600][B]Ejemplo de get_setting[/B][/COLOR]"))
    itemlist.append( Item(channel=__channel__, action="set_setting", title="[COLOR 0xFFEB7600][B]Ejemplo de set_setting[/B][/COLOR]"))

    return itemlist


def settingCanal(item):           
    ventana = guitools.show_settings(item.channel)
    return ventana


def dialogBox(item):      
    file_path= os.path.join(config.get_data_path(),__channel__+"_otros_datos.json")
    ventana = guitools.show_settings("test|mainlist",list_controls,  caption= "Titulo de la ventana", File_settings= file_path)
    
    return ventana
    
def get_setting(item):
    #name= 'fanart'
    name= 'pordedeuser'
    #name= 'nameControl2' # El parametro no existe
    #name= 'debug' # El parametro solo existe en la configuracion global
    value= config.get_setting(name,item.channel) # Pruebas en configuracion local
    #value= config.get_setting(name) # Pruebas en configuracion global
    guitools.dialog_ok(name, "El valor actual es: " + str(value))
    
    
def set_setting(item):
    import datetime
    now = str(datetime.datetime.now())
    name= 'pordedeuser'
    #name= 'nameControl22' # El parametro no existe
    ret= config.set_setting(name, now, item.channel) # Pruebas en configuracion local
    #ret= config.set_setting(name, now) # Pruebas en configuracion global
    if ret:
        mensaje = "El valor ha cambiado a: "
    else:
        mensaje = "El valor no se ha podido cambiar a: "
    guitools.dialog_ok(name, mensaje, now)
    
    