# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# tvalacarta - XBMC Plugin
# ------------------------------------------------------------
# channeltools
# Herramientas para trabajar con canales
# ------------------------------------------------------------

import os
import re

import config
import jsontools
import logger
import scrapertools
import jsontools


def is_adult(channel_name):
    logger.info("pelisalacarta.core.channeltools is_adult channel_name="+channel_name)

    channel_parameters = get_channel_parameters(channel_name)

    return channel_parameters["adult"] == "true"


def get_channel_parameters(channel_name):
    logger.info("pelisalacarta.core.channeltools get_channel_parameters channel_name="+channel_name)

    channel_xml = os.path.join(config.get_runtime_path(), 'channels', channel_name+".xml")

    if os.path.exists(channel_xml):
        logger.info("pelisalacarta.core.channeltools get_channel_parameters "+channel_name+".xml found")

        infile = open(channel_xml, "rb")
        data = infile.read()
        infile.close()

        # TODO: Pendiente del json :)
        channel_parameters = {}
        channel_parameters["title"] = scrapertools.find_single_match(data, "<name>([^<]*)</name>")
        channel_parameters["channel"] = scrapertools.find_single_match(data, "<id>([^<]*)</id>")
        channel_parameters["active"] = scrapertools.find_single_match(data, "<active>([^<]*)</active>")
        channel_parameters["adult"] = scrapertools.find_single_match(data, "<adult>([^<]*)</adult>")
        channel_parameters["language"] = scrapertools.find_single_match(data, "<language>([^<]*)</language>")
        channel_parameters["thumbnail"] = scrapertools.find_single_match(data, "<thumbnail>([^<]*)</thumbnail>")
        channel_parameters["bannermenu"] = scrapertools.find_single_match(data, "<bannermenu>([^<]*)</bannermenu>")
        channel_parameters["fanart"] = scrapertools.find_single_match(data, "<fanart>([^<]*)</fanart>")
        channel_parameters["include_in_global_search"] = scrapertools.find_single_match(
            data, "<include_in_global_search>([^<]*)</include_in_global_search>")
        channel_parameters["type"] = "generic"

        category_list = []
        matches = scrapertools.find_multiple_matches(data, "<category>([^<]*)</category>")
        for match in matches:
            category_list.append(match)

        channel_parameters["categories"] = category_list

        dict_tvshow_lang = dict()
        data = re.sub(r"\n|\r|\t|\s{2}", "", data)
        info = scrapertools.find_single_match(data, "<tvshow_lang>(.*?)</tvshow_lang>")

        if info:
            patron = "<(.*?)>(.*?)</[^>]+>"
            matches = re.compile(patron, re.DOTALL).findall(info)
            for key, value in matches:
                dict_tvshow_lang.update({key: value})

        channel_parameters["dict_tvshow_lang"] = dict_tvshow_lang

        list_quality = list()
        info = scrapertools.find_single_match(data, "<quality>(.*?)</quality>")
        if info:
            patron = "<item>(.*?)</item>"
            matches = re.compile(patron, re.DOTALL).findall(info)
            for value in matches:
                list_quality.append(value)

        channel_parameters["list_quality"] = list_quality

        logger.info("pelisalacarta.core.channeltools get_channel_parameters channel_parameters={chn}".
                    format(chn=channel_parameters))

    else:
        logger.info("pelisalacarta.core.channeltools get_channel_parameters "+channel_name+".xml NOT found")

        channel_parameters = dict()
        channel_parameters["adult"] = "false"

    return channel_parameters

def get_channel_json(channel_name):
    logger.info("pelisalacarta.core.channeltools get_channel_json channel_name="+channel_name)
    channel_xml =os.path.join(config.get_runtime_path() , 'channels' , channel_name + ".xml")
    channel_json = jsontools.xmlTojson(channel_xml)
    return channel_json['channel']
    
def get_channel_controls_settings(channel_name):    
    logger.info("pelisalacarta.core.channeltools get_channel_controls_settings channel_name="+channel_name)
    dict_settings= {}
    list_controls=[]
    
    settings= get_channel_json(channel_name)['settings']
    if type(settings) == list:
        list_controls = settings
    else:
        list_controls.append(settings)
        
    # Conversion de str a bool, etc...
    for c in list_controls:
        if not c.has_key('id') or not c.has_key('type') or not c.has_key('default'):
            # Si algun control de la lista  no tiene id, type o default lo ignoramos
            continue
        if not c.has_key('enabled') or c['enabled'] is None: 
            c['enabled']= True
        else:
            if c['enabled'].lower() == "true": c['enabled'] = True 
            elif c['enabled'].lower() == "false": c['enabled'] = False  
        if not c.has_key('visible') or c['visible'] is None: 
            c['visible']= True
        else:
            if c['visible'].lower() == "true": c['visible'] = True 
            elif c['visible'].lower() == "false": c['visible'] = False 
        if c['type'] == 'bool':
            c['default'] = True if c['default'].lower() == "true" else False
            
        if unicode(c['default']).isnumeric():
            c['default'] = int(c['default'])    
            
        dict_settings[c['id']] = c['default']
    
    return list_controls, dict_settings    
    
def get_channel_setting(name, channel):
    """
    Retorna el valor de configuracion del parametro solicitado.

    Devuelve el valor del parametro 'name' en la configuracion propia del canal 'channel'.
    
    Si se especifica el nombre del canal busca en la ruta \addon_data\plugin.video.pelisalacarta\settings_channels el archivo channel_data.json
    y lee el valor del parametro 'name'. Si el archivo channel_data.json no existe busca en la carpeta channels el archivo 
    channel.xml y crea un archivo channel_data.json antes de retornar el valor solicitado.
    
    Parametros:
    name -- nombre del parametro
    channel [ -- nombre del canal
      
    Retorna:
    value -- El valor del parametro 'name'
    
    """ 
    #Creamos la carpeta si no existe
    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
      os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))
      
    file_settings= os.path.join(config.get_data_path(), "settings_channels", channel+"_data.json")
    dict_settings ={}

    if os.path.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load_json(open(file_settings, "r").read())
            if dict_file.has_key('settings'): 
              dict_settings = dict_file['settings']
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: {0}".format(file_settings))

    if len(dict_settings) == 0 or not dict_settings.has_key(name):
        # Obtenemos controles del archivo ../channels/channel.xml
        from core import channeltools
        try:
          list_controls, default_settings = channeltools.get_channel_controls_settings(channel)
        except:
          default_settings = {}
                        
        if  default_settings.has_key(name): # Si el parametro existe en el channel.xml creamos el channel_data.json
            default_settings.update(dict_settings)
            dict_settings = default_settings
            dict_file = {}
            dict_file['settings']= dict_settings 
            # Creamos el archivo ../settings/channel_data.json
            json_data = jsontools.dump_json(dict_file)
            try:
                open(file_settings, "w").write(json_data)
            except EnvironmentError:
                logger.info("[config.py] ERROR al salvar el archivo: {0}".format(file_settings))

    # Devolvemos el valor del parametro local 'name' si existe
    if dict_settings.has_key(name):
      return dict_settings[name]
    else:
      return None

def set_channel_setting(name, value, channel):
    """
    Fija el valor de configuracion del parametro indicado.

    Establece 'value' como el valor del parametro 'name' en la configuracion propia del canal 'channel'.
    Devuelve el valor cambiado o None si la asignacion no se ha podido completar.
    
    Si se especifica el nombre del canal busca en la ruta \addon_data\plugin.video.pelisalacarta\settings_channels el archivo channel_data.json
    y establece el parametro 'name' al valor indicado por 'value'. 
    Si el parametro 'name' no existe lo añade, con su valor, al archivo correspondiente.
    
    
    Parametros:
    name -- nombre del parametro
    value -- valor del parametro
    channel -- nombre del canal
    
    Retorna:
    'value' en caso de que se haya podido fijar el valor y None en caso contrario
        
    """ 
    #Creamos la carpeta si no existe
    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
      os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))
      
    file_settings= os.path.join(config.get_data_path(), "settings_channels", channel+"_data.json")
    dict_settings ={}
            
    if os.path.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load_json(open(file_settings, "r").read())
            if dict_file.has_key('settings'): 
              dict_settings = dict_file['settings']
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: {0}".format(file_settings))
                
                           
    dict_settings[name] = value
    dict_file = {}
    dict_file['settings']= dict_settings
    # Creamos el archivo ../settings/channel_data.json
    try:
        open(file_settings, "w").write(jsontools.dump_json(dict_file))
    except EnvironmentError:
        logger.info("[config.py] ERROR al salvar el archivo: {0}".format(file_settings))
        return None

    return value
    
    
def get_channel_module(channel_name, package = "channels"):
    # Sustituye al que hay en servertools.py ...
    # ...pero anade la posibilidad de incluir un paquete diferente de "channels"
    if not package.endswith('.'): package +='.'
    logger.info("pelisalacarta.core.channeltools Importando " + package + channel_name)
    channels_module = __import__(package + channel_name)
    channel_module = getattr(channels_module,channel_name)
    logger.info("pelisalacarta.core.channeltools Importado " + package + channel_name)
    
    return channel_module
