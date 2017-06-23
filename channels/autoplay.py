# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta
# modulo para AutoPlay de pelisalacarta por Hernan_ar_c
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

from core import channeltools
from core import filetools
from core import config
from core import logger
from core.item import Item
from platformcode import platformtools
from core import jsontools
from core import servertools
from core import httptools
import os

__channel__ = "autoplay"

autoplay_node = {}


def context ():
    '''
    Agrega la opcion Configurar AutoPlay al menu contextual

    :return:
    '''

    _context = ""

    if config.is_xbmc():
        _context = [{"title": "Configurar AutoPlay",
                     "action": "autoplay_config",
                     "channel": "autoplay"
                     }
                    ]
    return _context


context = context()


def show_option (channel, itemlist):
    '''
    Agrega la opcion Configurar AutoPlay en la lista recibida

    :param channel: str
    :param itemlist: list (lista donde se desea integrar la opcion de configurar AutoPlay)
    :return:
    '''
    logger.info()
    plot_autoplay = 'AutoPlay permite auto reproducir los enlaces directamente, basándose en la configuracion de tus ' \
                    'servidores y calidades preferidas. '
    itemlist.append(
            Item(channel=__channel__, title="Configurar AutoPlay", action="autoplay_config", text_color='yellow',
                 thumbnail='https://s7.postimg.org/65ooga04b/Auto_Play.png',
                 fanart='https://s7.postimg.org/65ooga04b/Auto_Play.png', plot=plot_autoplay, from_channel=channel))
    return itemlist


def start (itemlist, item):
    '''
    Metodo principal desde donde se reproduce automaticamente los enlaces
    - En caso la opcion de personalizar activa utilizara las opciones definidas por el usuario.
    - En caso contrario intentara reproducir cualquier enlace que cuente con el idioma preferido.

    :param itemlist: list (lista de items listos para reproducir, o sea con action='play')
    :param item: item (el item principal del canal)
    :return: intenta autoreproducir, en caso de fallar devuelve el itemlist que recibio en un principio
    '''
    logger.info()
    global autoplay_node

    if not config.is_xbmc():
        platformtools.dialog_notification('AutoPlay ERROR', 'Sólo disponible para XBMC/Kodi')
        return itemlist
    else:
        if not autoplay_node:
            # Obtiene el nodo AUTOPLAY desde el json
            autoplay_node = filetools.get_node_from_data_json('autoplay', 'AUTOPLAY')

        # Agrega servidores y calidades que no estaban listados a autoplay_node
        new_options = check_value(item.channel, itemlist)

        # Obtiene el nodo del canal desde autoplay_node
        channel_node = autoplay_node.get(item.channel, {})
        # Obtiene los ajustes des autoplay para este canal
        settings_node = channel_node.get('settings', {})

        #logger.debug('channel_node: %s' % channel_node)
        #logger.debug('settings_node: %s' % settings_node)

        if settings_node['active']:
            url_list_valid = []
            autoplay_list = []
            favorite_servers = []
            favorite_quality = []

            # Guarda la accion del usuario
            user_config_setting = config.get_setting("default_action")

            # Habilita la accion reproducir en calidad alta si el servidor devuelve más de una calidad p.e. gdrive
            config.set_setting("default_action", "2")

            # Informa que AutoPlay esta activo
            platformtools.dialog_notification('AutoPlay Activo', '', sound=False)


            # Prioridades a la hora de ordenar itemlist:
            #       0: Servidores y calidades
            #       1: Calidades y servidores
            #       2: Solo servidores
            #       3: Solo calidades
            #       4: No ordenar
            if settings_node['custom_servers'] and settings_node['custom_quality']:
                priority = settings_node['priority'] # 0: Servidores y calidades o 1: Calidades y servidores
            elif settings_node['custom_servers']:
                priority = 2 # Solo servidores
            elif settings_node['custom_quality']:
                priority = 3 # Solo calidades
            else:
                priority = 4  # No ordenar


            # Obtiene las listas servidores, calidades disponibles desde el nodo del json de AutoPlay
            server_list = channel_node.get('servers', [])
            quality_list = channel_node.get('quality', [])

            #logger.debug('server_list: %s' % server_list)
            #logger.debug('quality_list: %s' % quality_list)


            # Se guardan los textos de cada servidor y calidad en listas p.e. favorite_servers = ['openload',
            # 'streamcloud']
            for num in range(1, 4):
                favorite_servers.append(channel_node['servers'][settings_node['server_%s' % num]])
                favorite_quality.append(channel_node['quality'][settings_node['quality_%s' % num]])



            # Se filtran los enlaces de itemlist y que se correspondan con los valores de autoplay
            for item in itemlist:
                autoplay_elem = dict()
                # Agrega la opcion configurar AutoPlay al menu contextual
                item.context.append({"title": "Configurar AutoPlay",
                                     "action": "autoplay_config",
                                     "channel": "autoplay",
                                     "from_channel": item.channel})

                # Si no tiene calidad definida le asigna calidad 'default'
                if item.quality == '':
                    item.quality = 'default'

                # Se crea la lista para configuracion personalizada
                if priority < 2 : # 0: Servidores y calidades o 1: Calidades y servidores

                    # si el servidor y la calidad no se encuentran en las listas de favoritos o la url esta repetida,
                    # descartamos el item
                    if item.server not in favorite_servers or item.quality not in favorite_quality \
                            or item.url in url_list_valid:
                        continue
                    autoplay_elem["indice_server"] = favorite_servers.index(item.server)
                    autoplay_elem["indice_quality"] = favorite_quality.index(item.quality)

                elif priority == 2: # Solo servidores

                    # si el servidor no se encuentra en la lista de favoritos o la url esta repetida,
                    # descartamos el item
                    if item.server not in favorite_servers or item.url in url_list_valid:
                        continue
                    autoplay_elem["indice_server"] = favorite_servers.index(item.server)

                elif priority == 3: # Solo calidades

                    # si la calidad no se encuentra en la lista de favoritos o la url esta repetida,
                    # descartamos el item
                    if item.quality not in favorite_quality or item.url in url_list_valid:
                        continue
                    autoplay_elem["indice_quality"] = favorite_quality.index(item.quality)

                else: # No ordenar

                    # si la url esta repetida, descartamos el item
                    if item.url in url_list_valid:
                        continue


                # Si el item llega hasta aqui lo añadimos al listado de urls validas y a autoplay_list
                url_list_valid.append(item.url)
                autoplay_elem['videoitem'] = item
                autoplay_elem['server'] = item.server # TODO only for debug
                autoplay_elem['quality'] = item.quality # TODO only for debug
                autoplay_list.append(autoplay_elem)


            logger.debug('autoplay_list: ' + str(autoplay_list))

            # Ordenamos segun la prioridad
            if priority == 0: # Servidores y calidades
                autoplay_list.sort(key=lambda orden: (orden['indice_server'],orden['indice_quality']))

            elif priority == 1: # Calidades y servidores
                autoplay_list.sort(key=lambda orden: (orden['indice_quality'], orden['indice_server']))

            elif priority == 2: # Solo servidores
                autoplay_list.sort(key=lambda orden: orden['indice_server'])

            elif priority == 3:  # Solo calidades
                autoplay_list.sort(key=lambda orden: orden['indice_quality'])

            logger.debug('autoplay_list: ' + str(autoplay_list))

            # TODO desde aqui hasta el final de la funcion no he podido mirarlo aun
            # Si hay elementos en la lista de autoplay se intenta reproducir cada elemento, hasta encontrar uno
            # funcional o fallen todos
            if autoplay_list:
                played = False
                max_intentos = 5
                max_intentos_servers = {}

                # Si se esta reproduciendo algo detiene la reproduccion
                if platformtools.is_playing():
                    platformtools.stop_video()
                for indice in autoplay_list:
                    if not platformtools.is_playing() and not played:
                        videoitem = indice['videoitem']

                        if not videoitem.server in max_intentos_servers:
                            max_intentos_servers[videoitem.server] = max_intentos

                        # Si se han alcanzado el numero maximo de intentos de este servidor saltamos al siguiente
                        if max_intentos_servers[videoitem.server] == 0:
                            continue

                        #logger.debug('item.language: ' + videoitem.language)
                        lang = " "
                        if hasattr(videoitem, 'language') and videoitem.language != "":
                            lang = " '%s' " % videoitem.language

                        platformtools.dialog_notification("AutoPlay", "%s%s%s" % (
                        videoitem.server.upper(), lang, videoitem.quality.upper()), sound=False)
                        #TODO videoitem.server es el id del server, pero podria no ser el nombre!!!

                        # Intenta reproducir los enlaces
                        # Si el canal tiene metodo play propio lo utiliza
                        channel = __import__('channels.%s' % item.channel, None, None, ["channels.%s" % item.channel])
                        if hasattr(channel, 'play'):
                            resolved_item = getattr(channel, 'play')(videoitem)
                            if len(resolved_item) > 0:
                                if isinstance(resolved_item[0], list):
                                    videoitem.video_urls= resolved_item
                                else:
                                    videoitem = resolved_item[0]

                        # si no directamente reproduce
                        #logger.debug('videoitem: ' + str(videoitem))
                        platformtools.play_video(videoitem)

                        try:
                            if platformtools.is_playing():
                                played = True
                                break
                        except:  # TODO evitar el informe de que el conector fallo o el video no se encuentra
                            logger.debug(str(len(autoplay_list)))

                        # Si hemos llegado hasta aqui es por q no se ha podido reproducir
                        max_intentos_servers[videoitem.server] -= 1

                        # Si se han alcanzado el numero maximo de intentos de este servidor
                        # preguntar si queremos seguir probando o lo ignoramos
                        if max_intentos_servers[videoitem.server] == 0:
                            text = "Parece que los enlaces de %s no estan funcionando." % videoitem.server.upper()
                            if not platformtools.dialog_yesno("AutoPlay", text,
                                                             "¿Desea ignorar todos los enlaces de este servidor?"):
                                max_intentos_servers[videoitem.server] = max_intentos

            else:
                platformtools.dialog_notification('AutoPlay No Fue Posible', 'No Hubo Coincidencias')
            if new_options:
                platformtools.dialog_notification("AutoPlay", "Nueva Calidad/Servidor disponible en la "
                                                  "configuracion", sound=False)

            # devuelve la lista de enlaces para la eleccion manual
            config.set_setting("default_action", user_config_setting)

        return itemlist


def prepare_autoplay_settings (channel, list_servers, list_quality): #TODO habria q repasar esto
    '''
    Prepara el json para que el canal puede utilizar AutoPlay
    :param channel: str
    :param list_servers: list (lista de servidores validos para el canal)
    :param list_quality: list (lista de calidades validas para el canal)
    :return:
    '''
    logger.info()

    fname = 'autoplay'
    autoplay_path = os.path.join(config.get_data_path(), "settings_channels")

    # Si no existe el json lo crea
    if not filetools.exists(autoplay_path):
        autoplay_node = {"AUTOPLAY": {}}
        filetools.write(autoplay_path + fname, jsontools.dump_json(autoplay_node))

    # Si la lista de calidades esta vacia se define una unica calidad default
    if len(list_quality) == 0:
        list_quality.append('default')

    # Se comprueba que no haya calidades ni servidores duplicados
    valid_quality = set(list_quality)
    valid_servers = set(list_servers)

    # Se define la lista de prioridades
    list_language = get_languages(channel) #TODO esto no se usa?

    # Se obtiene el nodo autoplay desde el json
    autoplay_node = filetools.get_node_from_data_json(fname, "AUTOPLAY")

    # Se Obtiene el nodo del canal desde el json
    channel_node = autoplay_node.get(channel, {})

    # Si el nodo esta vacio lo crea
    if len(channel_node) == 0:
        channel_settings = {
                            "servers": list(valid_servers),
                            "quality": list(valid_quality),
                            "settings": {
                                         "active": False,
                                         "custom_servers": False,
                                         "custom_quality": False,
                                         "priority": 0,
                                         "server_1": 0,
                                         "server_2": 0,
                                         "server_3": 0,
                                         "quality_1": 0,
                                         "quality_2": 0,
                                         "quality_3": 0
                                        }
                            }
        autoplay_node[channel] = channel_settings
        fname, json_data = filetools.update_json_data(autoplay_node, fname, 'AUTOPLAY')
        result = filetools.write(fname, json_data)

    return


def check_value (channel, itemlist):
    ''' comprueba la existencia de un valor en la lista de servidores o calidades
        si no existiera los agrega a la lista en el json

    :param channel: str
    :param values: list (una de servidores o calidades)
    :param value_type: str (server o quality)
    :return: list
    '''
    logger.info()
    global autoplay_node
    change = False

    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = filetools.get_node_from_data_json('autoplay', 'AUTOPLAY')


    channel_node = autoplay_node.get(channel)
    if not channel_node:
        # Si el canal no existe lo añadimos con la configuracion por defecto TODO repasar configuracion
        channel_node = autoplay_node[channel] = {"settings": {"active": True, "custom": False, "custom_servers": False,
                                                                "custom_quality": False, "priority": 0,
                                                                "server_1": 0, "server_2": 0, "server_3": 0,
                                                                "quality_1": 0, "quality_2": 0, "quality_3": 0}}
        change = True

    server_list = channel_node.get('servers')
    if not server_list:
        server_list = channel_node['servers'] = list()

    quality_list = channel_node.get('quality')
    if not quality_list:
        quality_list = channel_node['quality'] = list()


    for item in itemlist:
        if item.server not in server_list:
            server_list.append(item.server)
            change = True
        if item.quality not in quality_list:
            quality_list.append(item.quality)
            change = True


    if change: # TODO esto habra q cambiarlo cuando se muevan las funciones json a jsontools
        fname, json_data = filetools.update_json_data(autoplay_node, 'autoplay', 'AUTOPLAY')
        change = filetools.write(fname, json_data)

    return change


def autoplay_config(item):
    logger.info()
    global autoplay_node
    dict_values = {}
    list_controls = []


    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = filetools.get_node_from_data_json('autoplay', 'AUTOPLAY')

    channel_node = autoplay_node.get(item.from_channel, {})
    settings_node = channel_node.get('settings', {})

    allow_option = True


    active_settings = {"id": "active", "label": "AutoPlay (activar/desactivar la auto-reproduccion)",
                       "color": "0xffffff99", "type": "bool", "default": False, "enabled": allow_option,
                       "visible": allow_option}
    list_controls.append(active_settings)
    dict_values['active'] = settings_node.get('active', False) #TODO la manera correcta de fijar los valores del cuadro es asi, el atributo default fija el valor q tendra la primera vez y si se pulsa el boton 'Por defecto'


    # Idioma
    status_language = config.get_setting("filter_languages", item.from_channel) # TODO esto si
    if not status_language:
        status_language = 0

    set_language = {"id": "language", "label": "Idioma para AutoPlay (Obligatorio)", "color": "0xffffff99",
                    "type": "list", "default": 0, "enabled": "eq(-1,true)", "visible": True,
                    "lvalues": get_languages(item.from_channel)}

    list_controls.append(set_language)
    dict_values['language'] = status_language

    separador = {"id": "label", "label": "         "
                                         "_________________________________________________________________________________________",
                 "type": "label", "enabled": True, "visible": True}
    list_controls.append(separador)

    '''
    custom_status = settings_config.get('custom', False)
    # logger.debug('custom_status: ' + str(custom_status))
    custom_settings = {"id": "custom", "label": "   Personalizar Preferidos (Opcional)", "color": "0xff66ffcc",
                       "type": "bool", "default": custom_status, "enabled": "eq(-3,true)", "visible": True}
    list_controls.append(custom_settings)
    '''



    # Seccion servidores Preferidos
    server_list = channel_node.get("servers", [])
    if not server_list:
        enabled = False
        server_list = ["No disponible"]
    else:
        enabled = "eq(-3,true)"

    custom_servers_settings = {"id": "custom_servers", "label": "      Servidores Preferidos", "color": "0xff66ffcc",
                               "type": "bool", "default": False, "enabled": enabled, "visible": True}
    list_controls.append(custom_servers_settings)
    if dict_values['active'] and enabled:
        dict_values['custom_servers'] = settings_node.get('custom_servers', False)
    else:
        dict_values['custom_servers'] = False

    for num in range(1, 4):
        pos1 = num + 3
        default = num - 1
        if default > len(server_list) - 1:
            default = 0
        set_servers = {"id": "server_%s" % num, "label": u"          \u2665 Servidor Favorito %s" % num,
                       "color": "0xfffcab14", "type": "list", "default": default,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, num), "visible": True,
                       "lvalues": server_list}
        list_controls.append(set_servers)

        dict_values["server_%s" % num] = settings_node.get("server_%s" % num, 0)
        if settings_node.get("server_%s" % num, 0) > len(server_list) - 1:
            dict_values["server_%s" % num] = 0



    # Seccion Calidades Preferidas
    quality_list = channel_node.get("quality", [])
    if not quality_list:
        enabled = False
        quality_list = ["No disponible"]
    else:
        enabled = "eq(-7,true)"

    custom_quality_settings = {"id": "custom_quality", "label": "      Calidades Preferidas", "color": "0xff66ffcc",
                               "type": "bool", "default": False, "enabled": enabled, "visible": True}
    list_controls.append(custom_quality_settings)
    if dict_values['active'] and enabled:
        dict_values['custom_quality'] = settings_node.get('custom_quality', False)
    else:
        dict_values['custom_quality'] = False

    for num in range(1, 4):
        pos1 = num + 7
        default = num - 1
        if default > len(quality_list) - 1:
            default = 0

        set_quality = {"id": "quality_%s" % num, "label": u"          \u2665 Calidad Favorita %s" % num,
                       "color": "0xfff442d9", "type": "list", "default": default,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, num), "visible": True,
                       "lvalues": quality_list}
        list_controls.append(set_quality)
        dict_values["quality_%s" % num] = settings_node.get("quality_%s" % num, 0)
        if settings_node.get("quality_%s" % num, 0) > len(quality_list) - 1:
            dict_values["quality_%s" % num] = 0



    # Seccion Prioridades
    priority_list = ["Servidor y Calidad", "Calidad y Servidor"]
    set_priority = {"id": "priority", "label": "   Prioridad (Indica el orden para Auto-Reproducir)",
                    "color": "0xffffff99", "type": "list", "default": 0,
                    "enabled": True, "visible": "eq(-4,true)+eq(-8,true)+eq(-11,true)", "lvalues": priority_list}
    list_controls.append(set_priority)
    dict_values["priority"] = settings_node.get("priority", 0)


    # Abrir cuadro de dialogo
    platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values, callback='save',
                                        item=item, caption='AutoPlay') # TODO añadir el nombre del canal en el caption
    #TODO Prueba lo q hace el boton 'Por defecto' y dime si quieres mantenerlo o eliminarlo


def save(item, dict_data_saved): #TODO estaban invertidos!!!
    '''
    Guarda los datos de la ventana de configuracion
    
    :param item: item
    :param dict_data_saved: dict  
    :return:
    '''
    logger.info()
    global autoplay_node

    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = filetools.get_node_from_data_json('autoplay', 'AUTOPLAY')

    channel_node = autoplay_node.get(item.from_channel)
    config.set_setting("filter_languages", dict_data_saved.pop("language"), item.from_channel)
    channel_node['settings'] = dict_data_saved

    # TODO esto habra q cambiarlo cuando se muevan las funciones json a jsontools
    fname, json_data = filetools.update_json_data(autoplay_node, 'autoplay', 'AUTOPLAY')
    ret = filetools.write(fname, json_data)

    return ret


def get_languages(channel):
    '''
    Obtiene los idiomas desde el xml del canal

    :param channel: str
    :return: list
    '''
    logger.info()
    list_language =['No filtrar']
    list_controls, dict_settings = channeltools.get_channel_controls_settings(channel)
    for control in list_controls:
        #logger.debug('control: %s' % control)
        if control["id"] == 'filter_languages':
            list_language = control["lvalues"]

    return list_language

'''
# Metodos auxiliares for debug
def make_server_list (itemlist):
    """

    :param itemlist: list (lista de elementos que contenga el nombre del servidor)
    :return: log con una lista de servidores
    """
    logger.info()
    server_list = []
    new_serverlist = []

    for item in itemlist:
        data = httptools.downloadpage(item.url).data
        new_serverlist.extend(servertools.find_video_items(data=data))

    for item in new_serverlist:
        if item.server not in server_list:
            server_list.append(item.server)
    logger.debug('server_list: ' + str(server_list))

def check_status (channel):

    logger.info()

    fname = 'autoplay'
    # Obtenemos el estado de AutoPlay desde el json
    autoplay_node = filetools.get_node_from_data_json(fname, 'AUTOPLAY')
    channel_node = autoplay_node.get(channel, {})
    settings_node = channel_node.get('settings', {})
    result = settings_node.get('active', False)
    return result

'''