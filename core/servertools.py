﻿# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta 4
# Copyright 2015 tvalacarta@gmail.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# This file is part of pelisalacarta 4.
#
# pelisalacarta 4 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pelisalacarta 4 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pelisalacarta 4.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------------------
# Server management
#------------------------------------------------------------

import os
import re
import time
import datetime
from core import jsontools
from core import config
from core import logger
from core import httptools
from core.item import Item
from platformcode import platformtools
import urlparse

dict_servers_parameters = {}

def find_video_items(item=None, data=None):
    """
    Función genérica para buscar vídeos en una página, devolviendo un itemlist con los items listos para usar.
     - Si se pasa un Item como argumento, a los items resultantes mantienen los parametros del item pasado
     - Si no se pasa un Item, se crea uno nuevo, pero no contendra ningun parametro mas que los propios del servidor.

    @param item: Item al cual se quieren buscar vídeos, este debe contener la url válida
    @type item: Item
    @param data: Cadena con el contendio de la página ya descargado (si no se pasa item)
    @type data: str

    @return: devuelve el itemlist con los resultados
    @rtype: list
    """
    logger.info()
    itemlist = []
    
    # Descarga la página
    if data is None:
        data = httptools.downloadpage(item.url).data
    
    #Crea un item si no hay item    
    if item is None:
        item = Item()
    #Pasa los campos thumbnail y title a contentThumbnail y contentTitle
    else:
        if not item.contentThumbnail:
            item.contentThumbnail = item.thumbnail
        if not item.contentTitle:
            item.contentTitle = item.title

    # Busca los enlaces a los videos
    for label, url, server, thumbnail in findvideos(data):
        title = "Enlace encontrado en %s" % label
        itemlist.append(item.clone(title=title, action="play", url=url, thumbnail=thumbnail, server=server, folder=False))

    return itemlist


def get_servers_itemlist(itemlist, fnc=None, sort=False):
    """
    Obtiene el servidor para cada uno de los items, en funcion de su url.
     - Asigna el servidor, la url modificada, el thumbnail (si el item no contiene contentThumbnail se asigna el del thumbnail)
     - Si se pasa una funcion por el argumento fnc, esta se ejecuta pasando el item como argumento,
       el resultado de esa funcion se asigna al titulo del item
       - En esta funcion podemos modificar cualquier cosa del item
       - Esta funcion siempre tiene que devolver el item.title como resultado
     - Si no se encuentra servidor para una url, se asigna "directo"
     
    @param itemlist: listado de items
    @type itemlist: list
    @param fnc: función para ejecutar con cada item (para asignar el titulo)
    @type fnc: function
    """
    server_stats = {}
    #Recorre los servidores
    for serverid in get_servers_list().keys():
        server_parameters = get_server_parameters(serverid)
        
        #Recorre los patrones
        for pattern in server_parameters.get("find_videos", {}).get("patterns", []):
            logger.info(pattern["pattern"])
            #Recorre los resultados
            for match in re.compile(pattern["pattern"], re.DOTALL).finditer("\n".join([item.url.split('|')[0] for item in itemlist if not item.server])):
                url= pattern["url"]
                for x in range(len(match.groups())):
                    url = url.replace("\\%s" % (x+1), match.groups()[x])
                    
                server_stats[serverid] = "found"
                for item in itemlist:
                    if match.group() in item.url:
                        if not item.contentThumbnail:
                            item.contentThumbnail = item.thumbnail
                        item.thumbnail = server_parameters.get("thumbnail", "")
                        item.server = serverid
                        if '|' in item.url:
                            item.url = url + '|' + item.url.split('|')[1]
                        else:
                            item.url = url
                        
    save_server_stats(server_stats, "find_videos")
    
    #Eliminamos los servidores desactivados
    itemlist = filter(lambda i: not i.server or is_server_enabled(i.server), itemlist)
    
    for item in itemlist:
        #Asignamos "directo" en caso de que el server no se encuentre en pelisalcarta
        if not item.server and item.url:
            item.server = "directo"
                
        if fnc:
            item.title = fnc(item)

    # Filtrar si es necesario
    itemlist = filter_servers(itemlist)
    
    # Ordenar segun favoriteslist si es necesario
    if sort:
        itemlist = sort_servers(itemlist)
    
    return itemlist

def findvideos(data, skip=False):
    """
    Recorre la lista de servidores disponibles y ejecuta la funcion findvideosbyserver para cada uno de ellos
    :param data: Texto donde buscar los enlaces
    :param skip: Indica un limite para dejar de recorrer la lista de servidores. Puede ser un booleano en cuyo caso
    seria False para recorrer toda la lista (valor por defecto) o True para detenerse tras el primer servidor que
    retorne algun enlace. Tambien puede ser un entero mayor de 1, que representaria el numero maximo de enlaces a buscar.
    :return:
    """
    logger.info()
    devuelve = []
    skip = int(skip)
    servers_list = get_servers_list().keys()

    # Ordenar segun favoriteslist si es necesario
    servers_list = sort_servers(servers_list)
    is_filter_servers = False
    
    # Ejecuta el findvideos en cada servidor activo
    for serverid in servers_list:
        if not is_server_enabled(serverid):
            continue
        if  config.get_setting("black_list", server=serverid):
            is_filter_servers = True
            continue

        devuelve.extend(findvideosbyserver(data, serverid))
        if skip and len(devuelve) >= skip:
            devuelve = devuelve[:skip]
            break

    if not devuelve and is_filter_servers:
        platformtools.dialog_ok("Filtrar servidores (Lista Negra)",
                                "No hay enlaces disponibles que cumplan los requisitos de su Lista Negra.",
                                "Pruebe de nuevo modificando el fíltro en 'Configuracíon Servidores")

    return devuelve


def findvideosbyserver(data, serverid):
    serverid = get_server_name(serverid)
    server_parameters = get_server_parameters(serverid)
    devuelve = []
    
    if server_parameters.has_key("find_videos"):
        #Recorre los patrones
        for pattern in server_parameters["find_videos"].get("patterns", {}):
            msg = "%s\npattern: %s" % (serverid, pattern["pattern"])
            #Recorre los resultados
            for match in re.compile(pattern["pattern"], re.DOTALL).finditer(data):
                url= pattern["url"]
                #Crea la url con los datos
                for x in range(len(match.groups())):
                    url = url.replace("\\%s" % (x+1), match.groups()[x])
                msg += "\nurl encontrada: %s" % url
                value = server_parameters["name"], url, serverid, server_parameters.get("thumbnail", "")
                if not value in devuelve and not url in server_parameters["find_videos"].get("ignore_urls", []):
                    devuelve.append(value)
                logger.info(msg)
                
    else: # TODO eliminar esto cuando todos los xml esten actualizados
        # Sistema antiguo find_videos en py
        try:
            servers_module = __import__("servers." + serverid)
            server_module = getattr(servers_module, serverid)
            result = server_module.find_videos(data)
            devuelve = [[server_parameters["name"], d[1], d[2], server_parameters.get("thumbnail", "")] for d in devuelve]
            devuelve.extend(result)
        except ImportError:
            logger.info("No existe conector para #" + serverid + "#")
        except:
            logger.info("Error en el conector #" + serverid + "#")
            import traceback
            logger.info(traceback.format_exc())
    
    #Guardar estadisticas
    if devuelve:
        save_server_stats({serverid: "found"}, "find_videos")
        
    return devuelve


def guess_server_thumbnail(serverid):
    server = get_server_name(serverid)
    server_parameters = get_server_parameters(server)
    return server_parameters.get('thumbnail', "")


def get_server_from_url(url):
    encontrado = findvideos(url, True)
    if len(encontrado)>0:
        devuelve = encontrado[0][2]
    else:
        devuelve = "directo"

    return devuelve


def resolve_video_urls_for_playing(server, url, video_password="", muestra_dialogo=False):
    """
    Función para obtener la url real del vídeo
    @param server: Servidor donde está alojado el vídeo
    @type server: str
    @param url: url del vídeo
    @type url: str
    @param video_password: Password para el vídeo
    @type video_password: str
    @param muestra_dialogo: Muestra el diálogo de progreso
    @type muestra_dialogo: bool

    @return: devuelve la url del video
    @rtype: list
    """
    logger.info("Server: %s, Url: %s" % (server, url))
    
    server = server.lower()
    
    video_urls = []
    video_exists = True
    error_messages = []
    
    # Si el vídeo es "directo" o "local", no hay que buscar más
    if server=="directo" or server=="local":
        logger.info("Server: %s, la url es la buena" % server)
        video_urls.append([ "%s [%s]" % (urlparse.urlparse(url)[2][-4:], server) , url ])

    # Averigua la URL del vídeo
    else:
        server_parameters = get_server_parameters(server)
        
        # Muestra un diágo de progreso
        if muestra_dialogo:
            progreso = platformtools.dialog_progress("pelisalacarta", "Conectando con %s" % server_parameters["name"])

        #Cuenta las opciones disponibles, para calcular el porcentaje
        opciones = []
        orden = [["free"] + [server] + [premium for premium in server_parameters["premium"] if not premium == server],
                 [server] + [premium for premium in server_parameters["premium"] if not premium == server] + ["free"],
                 [premium for premium in server_parameters["premium"] if not premium == server] + [server] + ["free"]
                ]
        
        if server_parameters:
            if server_parameters["free"] == "true": opciones.append("free")
            opciones.extend([premium for premium in server_parameters["premium"] if config.get_setting("premium",server=premium)])
            
            priority = int(config.get_setting("resolve_priority"))
            opciones = sorted(opciones, key=lambda x: orden[priority].index(x))
            
            
            logger.info("Opciones disponibles: %s | %s"  % (len(opciones), opciones))
        else:
            logger.error("No existe conector para el servidor %s" % server)
            error_messages.append("No existe conector para el servidor %s" % server)

        #Importa el server
        try:
            server_module = __import__('servers.%s' % server, None, None, ["servers.%s" % server])
            logger.info("Servidor importado: %s" % server_module)
        except:
            server_module = None
            logger.error("No se ha podido importar el servidor: %s" % server)
            import traceback
            logger.error(traceback.format_exc())
            

        # Si tiene una función para ver si el vídeo existe, lo comprueba ahora
        if hasattr(server_module, 'test_video_exists'):
            logger.info("Invocando a %s.test_video_exists" % server)
            try:
                video_exists, message = server_module.test_video_exists(page_url=url)
                
                if not video_exists:
                    error_messages.append(message)
                    logger.info("test_video_exists dice que el video no existe")
                else:
                    logger.info("test_video_exists dice que el video SI existe")
            except:
                logger.error("No se ha podido comprobar si el video existe")
                import traceback
                logger.error(traceback.format_exc())
        
        #Si el video existe y el modo free está disponible, obtenemos la url
        if video_exists:
            for opcion in opciones:
                #Opcion free y premium propio usa el mismo server
                if opcion == "free" or opcion == server:
                    serverid = server_module
                    server_name = server_parameters["name"]
                    
                #Resto de opciones premium usa un debrider
                else:
                    serverid = __import__('servers.debriders.%s' % opcion, None, None, ["servers.debriders.%s" % opcion])
                    server_name = get_server_parameters(opcion)["name"]
                
                #Muestra el progreso
                if muestra_dialogo:
                  progreso.update((100 / len(opciones)) * opciones.index(opcion)  , "Conectando con %s" % server_name)
                
                #Modo free
                if opcion == "free":
                    try:
                        logger.info("Invocando a %s.get_video_url" % server)
                        response = serverid.get_video_url(page_url=url, video_password=video_password)
                        if response:
                            save_server_stats({server: "sucess"}, "resolve")                           
                        video_urls.extend(response)
                    except:
                        save_server_stats({server: "error"}, "resolve")  
                        logger.error("Error al obrener la url en modo free")
                        error_messages.append("Se ha producido un error en %s" % server_name)
                        import traceback
                        logger.error(traceback.format_exc())
                        
                #Modo premium        
                else:        
                    try:
                        logger.info("Invocando a %s.get_video_url" % opcion)
                        response = serverid.get_video_url(page_url=url, premium=True, user=config.get_setting("user", server=opcion), password=config.get_setting("password", server=opcion), video_password=video_password)
                        if response and response[0][1]:
                            if opcion == server:
                                save_server_stats({server: "sucess"}, "resolve")
                            video_urls.extend(response)
                        elif response and response[0][0]:
                            error_messages.append(response[0][0])
                        else:
                            error_messages.append("Se ha producido un error en %s" % server_name)
                    except:
                        if opcion == server:
                            save_server_stats({server: "error"}, "resolve")
                        logger.error("Error en el servidor: %s" % opcion)
                        error_messages.append("Se ha producido un error en %s" % server_name)
                        import traceback
                        logger.error(traceback.format_exc())
                
                #Si ya tenemos URLS, dejamos de buscar
                if video_urls and config.get_setting("resolve_stop") == "true":
                    break
                
            #Cerramos el progreso
            if muestra_dialogo:
                progreso.update( 100 , "Proceso finalizado")
                progreso.close()
            
            #Si no hay opciones disponibles mostramos el aviso de las cuentas premium
            if video_exists and not opciones and server_parameters.get("premium"):
                listapremium = [get_server_parameters(premium)["name"] for premium in server_parameters["premium"]]
                error_messages.append("Para ver un vídeo en %s necesitas<br/>una cuenta en: %s" % (server, " o ".join(listapremium)))
            
            #Si no tenemos urls ni mensaje de error, ponemos uno generico            
            elif not video_urls and not error_messages:
                error_messages.append("Se ha producido un error en %s" % get_server_parameters(server)["name"])

    
    return video_urls, len(video_urls) > 0, "<br/>".join(error_messages)


def get_server_name(serverid):
    """
    Función obtener el nombre del servidor real a partir de una cadena.
    @param serverid: Cadena donde mirar
    @type serverid: str

    @return: Nombre del servidor
    @rtype: str
    """
    serverid = serverid.lower().split(".")[0]
    
    #Obtenemos el listado de servers
    server_list = get_servers_list().keys()
    
    #Si el nombre está en la lista
    if serverid in server_list: 
        return serverid
    
    #Recorre todos los servers buscando el nombre
    for server in server_list:
        params = get_server_parameters(server)
        #Si la nombre esta en el listado de ids
        if serverid in params["id"]:
            return server
        #Si el nombre es mas de una palabra, comprueba si algun id esta dentro del nombre:
        elif len(serverid.split()) > 1:
            for id in params["id"]:
                if id in serverid:
                    return server
    
    #Si no se encuentra nada se devuelve una cadena vacia
    return ""


def is_server_enabled(server):
    """
    Función comprobar si un servidor está segun la configuración establecida
    @param server: Nombre del servidor
    @type server: str

    @return: resultado de la comprobación
    @rtype: bool
    """
    
    server = get_server_name(server)

    #El server no existe
    if not server:
        return False
        
    server_parameters = get_server_parameters(server)
    if server_parameters["active"] == "true":
        if not config.get_setting("hidepremium"):
            return True
        elif server_parameters["free"] == "true":
            return True
        elif [premium for premium in server_parameters["premium"] if config.get_setting("premium",server=premium)]:
            return True

    return False

        
def get_server_parameters(server):
    """
    Obtiene los datos del servidor
    @param server: Nombre del servidor
    @type server: str

    @return: datos del servidor
    @rtype: dict
    """
    global dict_servers_parameters
    server = server.split('.')[0]
    
    if not server in dict_servers_parameters:
        try:
            #Servers
            if os.path.isfile(os.path.join(config.get_runtime_path(),"servers", server + ".xml")):
                JSONFile =  xml2dict(os.path.join(config.get_runtime_path(),"servers", server + ".xml"))["server"]
            #Debriders
            elif os.path.isfile(os.path.join(config.get_runtime_path(),"servers", "debriders", server + ".xml")):
                JSONFile =  xml2dict(os.path.join(config.get_runtime_path(),"servers", "debriders", server + ".xml"))["server"]
            
            
            for k in ['premium', 'id']:
                if not JSONFile.has_key(k) or JSONFile[k] == "":
                    JSONFile[k] = []
                elif type(JSONFile[k]) == dict:
                    JSONFile[k] = JSONFile[k]["value"]
                if type(JSONFile[k]) == str:
                    JSONFile[k] = [JSONFile[k]]
                    
            if JSONFile.has_key('find_videos'):
                if type(JSONFile['find_videos']['patterns']) == dict:
                    JSONFile['find_videos']['patterns'] = [JSONFile['find_videos']['patterns']]
                
                if not JSONFile['find_videos'].get("ignore_urls", ""):
                    JSONFile['find_videos']["ignore_urls"] = []
                elif type(JSONFile['find_videos']["ignore_urls"] == dict):
                    JSONFile['find_videos']["ignore_urls"] = JSONFile['find_videos']["ignore_urls"]["value"]
                if type(JSONFile['find_videos']["ignore_urls"]) == str:
                    JSONFile['find_videos']["ignore_urls"] = [JSONFile['find_videos']["ignore_urls"]]
                    
            if JSONFile.has_key('settings'):
                if type(JSONFile['settings']) == dict:
                    JSONFile['settings'] = [JSONFile['settings']]
            
                if len(JSONFile['settings']):
                    JSONFile['has_settings'] = True
                else:
                    JSONFile['has_settings'] = False
            else:
                JSONFile['has_settings'] = False

            dict_servers_parameters[server] = JSONFile

        except:
            mensaje = "Error al cargar el servidor: %s\n" % server
            import traceback
            logger.error(mensaje + traceback.format_exc())
            return {}
    
    import copy
    return copy.deepcopy(dict_servers_parameters[server])


def get_server_controls_settings(server_name):
    dict_settings = {}

    list_controls = get_server_parameters(server_name).get('settings',[])

    # Conversion de str a bool, etc...
    for c in list_controls:
        if 'id' not in c or 'type' not in c or 'default' not in c:
            # Si algun control de la lista  no tiene id, type o default lo ignoramos
            continue
        
        c['enabled'] = [True, False][c.get('enabled', '').lower() == "false"]
        c['visible'] = [True, False][c.get('visible', '').lower() == "false"]
        
        if c['type'] == 'bool':
            c['default'] = [True, False][c.get('default', '').lower() == "false"]

        if unicode(c['default']).isnumeric():
            c['default'] = int(c['default'])

        dict_settings[c['id']] = c['default']

    return list_controls, dict_settings


def get_server_setting(name, server):

    # Creamos la carpeta si no existe
    if not os.path.exists(os.path.join(config.get_data_path(), "settings_servers")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_servers"))

    file_settings = os.path.join(config.get_data_path(), "settings_servers", server+"_data.json")
    dict_settings = {}
    dict_file = {}
    if os.path.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load_json(open(file_settings, "rb").read())
            if isinstance(dict_file, dict) and 'settings' in dict_file:
                dict_settings = dict_file['settings']
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: %s" % file_settings)

    if len(dict_settings) == 0 or name not in dict_settings:
        # Obtenemos controles del archivo ../channels/channel.xml
        try:
            list_controls, default_settings = get_server_controls_settings(server)
        except:
            default_settings = {}
        if name in default_settings:  # Si el parametro existe en el channel.xml creamos el channel_data.json
            default_settings.update(dict_settings)
            dict_settings = default_settings
            dict_file['settings'] = dict_settings
            # Creamos el archivo ../settings/channel_data.json
            json_data = jsontools.dump_json(dict_file)
            try:
                open(file_settings, "wb").write(json_data)
            except EnvironmentError:
                logger.info("ERROR al salvar el archivo: %s" % file_settings)

    # Devolvemos el valor del parametro local 'name' si existe
    if name in dict_settings:
        return dict_settings[name]
    else:
        return None


def set_server_setting(name, value, server):
    # Creamos la carpeta si no existe
    if not os.path.exists(os.path.join(config.get_data_path(), "settings_servers")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_servers"))

    file_settings = os.path.join(config.get_data_path(), "settings_servers", server + "_data.json")
    dict_settings = {}

    dict_file = None

    if os.path.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load_json(open(file_settings, "r").read())
            dict_settings = dict_file.get('settings', {})
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: %s" % file_settings)

    dict_settings[name] = value

    # comprobamos si existe dict_file y es un diccionario, sino lo creamos
    if dict_file is None or not dict_file:
        dict_file = {}

    dict_file['settings'] = dict_settings

    # Creamos el archivo ../settings/channel_data.json
    try:
        json_data = jsontools.dump_json(dict_file)
        open(file_settings, "w").write(json_data)
    except EnvironmentError:
        logger.info("ERROR al salvar el archivo: %s" % file_settings)
        return None

    return value
    
    
def get_servers_list():
    """
    Obtiene un diccionario con todos los servidores disponibles

    @return: Diccionario cuyas claves son los nombre de los servidores (nombre del xml)
    y como valor un diccionario con los parametros del servidor.
    @rtype: dict
    """
    server_list = {}
    for server in os.listdir(os.path.join(config.get_runtime_path(),"servers")):
        if server.endswith(".xml") and not server == "version.xml":
            server_parameters = get_server_parameters(server)
            if server_parameters["active"] == "true":
                server_list[server.split(".")[0]] = server_parameters
    
    return server_list

    
def get_debriders_list():
    """
    Obtiene un diccionario con todos los debriders disponibles

    @return: Diccionario cuyas claves son los nombre de los debriders (nombre del xml)
    y como valor un diccionario con los parametros del servidor.
    @rtype: dict
    """
    server_list = {}
    for server in os.listdir(os.path.join(config.get_runtime_path(),"servers", "debriders")):
        if server.endswith(".xml"):
            server_parameters = get_server_parameters(server)
            if server_parameters["active"] == "true":
                logger.info(server_parameters)
                server_list[server.split(".")[0]] = server_parameters
    return server_list
    

def sort_servers(servers_list):
    """
    Si existe un listado de servidores favoritos en la configuracion lo utiliza para ordenar la lista servers_list
    :param servers_list: Listado de servidores para ordenar. Los elementos de la lista servers_list pueden ser strings
    u objetos Item. En cuyo caso es necesario q tengan un atributo item.server del tipo str.
    :return: Lista del mismo tipo de objetos que servers_list ordenada en funcion de los servidores favoritos.
    """
    if servers_list:
        if isinstance(servers_list[0],Item):
            servers_list = sorted(servers_list, key = lambda x: config.get_setting("white_list",server=x.server) or 100)
        else:
            servers_list = sorted(servers_list, key = lambda x: config.get_setting("white_list",server=x) or 100)
    return servers_list

    
def filter_servers(servers_list):
    """
    Si esta activada la opcion "Filtrar servidores (Lista Negra)" en la configuracion, elimina de la lista de entrada los
    servidores incluidos en la Lista Negra.
    :param servers_list: Listado de servidores para filtrar. Los elementos de la lista servers_list pueden ser strings
    u objetos Item. En cuyo caso es necesario q tengan un atributo item.server del tipo str.
    :return: Lista del mismo tipo de objetos que servers_list filtrada en funcion de la Lista Negra.
    """
    servers_list_filter = []
    if servers_list:
        if isinstance(servers_list[0],Item):
            servers_list_filter = filter(lambda x: not config.get_setting("black_list",server=x.server), servers_list)
        else:
            servers_list_filter = filter(lambda x: not config.get_setting("black_list",server=x), servers_list)
            
        # Si no hay enlaces despues de filtrarlos
        if not servers_list_filter and platformtools.dialog_yesno("Filtrar servidores (Lista Negra)",
                                                                  "Todos los enlaces disponibles pertenecen a servidores incluidos en su Lista Negra.",
                                                                  "¿Desea mostrar estos enlaces?"):
            return servers_list
    return servers_list_filter


def xml2dict(file = None, xmldata = None):
      import re, sys, os
      parse = globals().get(sys._getframe().f_code.co_name)

      if xmldata == None and file == None:  raise Exception("No hay nada que convertir!")
      if xmldata == None:
        if not os.path.exists(file): raise Exception("El archivo no existe!")
        xmldata = open(file, "rb").read()

      matches = re.compile("<(?P<tag>[^>]+)>[\n]*[\s]*[\t]*(?P<value>.*?)[\n]*[\s]*[\t]*<\/(?P=tag)\s*>",re.DOTALL).findall(xmldata)

      return_dict = {}
      for tag, value in matches:
        #Si tiene elementos
        if "<" and "</" in value:
          if tag in return_dict:
            if type(return_dict[tag])== list:
              return_dict[tag].append(parse(xmldata=value))
            else:
              return_dict[tag] = [return_dict[tag]]
              return_dict[tag].append(parse(xmldata=value))
          else:
              return_dict[tag] = parse(xmldata=value)

        else:
          if tag in return_dict:
            if type(return_dict[tag])== list:
              return_dict[tag].append(value)
            else:
              return_dict[tag] = [return_dict[tag]]
              return_dict[tag].append(value)
          else:
            return_dict[tag] = value
      return return_dict

    
def save_server_stats(stats, type="find_videos"):
    if not config.get_setting("server_stats"):
        return
        
    stats_file = os.path.join(config.get_data_path(), "server_stats.json")
    today = datetime.datetime.now().strftime ("%Y%m%d")
    
    #Leemos el archivo
    try:
        server_stats= jsontools.load_json(open(stats_file, "rb").read())
    except:
        server_stats = {"created": time.time(), "data": {}}
    
    #Actualizamos los datos
    for server in stats:
        if not server in server_stats["data"]:
            server_stats["data"][server]= {}
        
        if not today in server_stats["data"][server]:
            server_stats["data"][server][today] = {"find_videos": {"found": 0}, "resolve": {"sucess": 0, "error": 0}}
            
        server_stats["data"][server][today][type][stats[server]] += 1
     
    #Guardamos el archivo            
    open(stats_file, "wb").write(jsontools.dump_json(server_stats))
    
    #Enviamos al servidor
    return
    if time.time() - server_stats["created"] > 86400: #86400: #1 Dia
        from core import httptools
        if httptools.downloadpage("url servidor", headers= {'Content-Type': 'application/json'}, post=jsontools.dump_json(server_stats)).sucess:
            os.remove(stats_file)
            logger.info("Datos enviados correctamente")
        else:
            logger.info("No se han podido enviar los datos")

