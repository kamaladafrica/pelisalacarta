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
            Item(channel=__channel__, title="[COLOR yellow]Configurar AutoPlay[/COLOR]", action="autoplay_config",
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
    :return: intenta autoreproducir, en caso de fallar devielve el itemlist que recibio en un principio
    '''
    logger.info()

    if not config.is_xbmc():
        platformtools.dialog_notification('AutoPlay ERROR', 'Sólo disponible para XBMC/Kodi')
        return itemlist
    else:

        # Obtiene el nodo del canal desde el json de AutoPlay
        autoplay_node = filetools.get_node_from_data_json('autoplay', 'AUTOPLAY')
        channel_node = autoplay_node.get(item.channel, {})
        settings_node = channel_node.get('settings', {})

        #logger.debug('channel_node: %s' % channel_node)
        #logger.debug('settings_node: %s' % settings_node)

        if settings_node['active']:
            url_list_valid = []
            autoplay_list = []
            favorite_servers = []
            favorite_quality = []
            # Agrega servidores que no estaban listados
            for item in itemlist:
                channel_servers = check_value(item.channel, item.server, 'servers')
                channel_quality = check_value(item.channel, item.quality, 'quality')

            # Guarda la accion del usuario
            user_config_setting = config.get_setting("default_action")

            # Habilita la accion reproducir en calidad alta si el servidor devuelve más de una calidad p.e. gdrive
            config.set_setting("default_action", "2")

            # Informa que AutoPlay esta activo
            platformtools.dialog_notification('AutoPlay Activo', '', sound=False)

            # Obtenemos si tenemos configuración personalizada
            autoplay_settings = settings_node.get('custom', False)
            #logger.debug ('autoplay_settings: '+str(autoplay_settings))

            if autoplay_settings:
                # Ordena los enlaces por la prioridad Servidor/Calidad la lista de favoritos
                favorite_priority = settings_node.get("priority", 0)
            else:
                # Si no está activa la personalización, la prioridad se fija en calidad
                favorite_priority = 2

            # Obtiene las listas servidores, calidades disponibles desde el nodo del json de AutoPlay

            server_list = channel_node.get('servers', [])
            quality_list = channel_node.get('quality', [])

            #logger.debug('server_list: %s' % server_list)
            #logger.debug('quality_list: %s' % quality_list)

            # Se guardan los textos de cada servidor y calidad en listas p.e. favorite_servers = ['openload',
            # 'streamcloud']
            for num in range(1, 4):
                #logger.debug('server_list: %s ' % server_list[settings_node.get("server_%s" % num, 0)])
                # logger.debug('config_get_settings: %s ' % config.get_setting("server_%s" % num, item.channel))

                favorite_servers.append(server_list[settings_node.get("server_%s" % num, 0)])
                favorite_quality.append(quality_list[settings_node.get("quality_%s" % num, 0)])

            # Se filtran los enlaces de itemlist y que se correspondan con los valores de autoplay
            for item in itemlist:
                # Agrega la opcion configurar AutoPlay al menu contextual
                item.context.append({"title": "Configurar AutoPlay",
                                     "action": "autoplay_config",
                                     "channel": "autoplay",
                                     "from_channel": item.channel
                                     }
                                    )
                # Si no tiene calidad definida le asigna calidad 'default'
                if item.quality == '':
                    item.quality = 'default'
                # Se crea la lista para configuracion personalizada
                if autoplay_settings:
                    # si el servidor no se encuentra en la lista de favoritos o la url no es correcta, avanzamos en
                    # el bucle
                    if item.server not in favorite_servers or item.url in url_list_valid:
                        continue
                    else:
                        url_list_valid.append(item.url)
                        is_quality_valid = True

                        # si item tiene propiedad quality se obtiene su valor y si está dentro de los favoritos,
                        # se valida
                        if hasattr(item, 'quality'):
                            if item.quality in favorite_quality:
                                is_quality_valid = True
                            else:
                                is_quality_valid = False

                        # la calidad es correcta, tanto si está dentro de los valores permitidos, como si no existe,
                        # ya que si no existe el valor no se puede filtrar por él.
                        if is_quality_valid:
                            autoplay_list.append(
                                    [favorite_servers.index(item.server), item, favorite_quality.index(item.quality),
                                     item.quality, item.server])

                else:
                    is_quality_valid = True
                    if hasattr(item, 'quality'):
                        if item.quality in quality_list:
                            is_quality_valid = True
                        else:
                            is_quality_valid = False

                    # TODO esto hay que revisarlo, no me quedo del todo conforme, aquí filtra por los servidores que
                    # existan
                    # en el xml y no debería ser así, debería obtener cualquiera es decir la siguiente linea
                    # comentada...
                    # if is_quality_valid:
                    if is_quality_valid and item.server in server_list:
                        autoplay_list.append(
                                [server_list.index(item.server), item, quality_list.index(item.quality), item.quality,
                                 item.server])

            # Se ordena la lista solo por calidad
            if favorite_priority == 2:
                autoplay_list.sort(key=lambda priority: priority[2])

            # Se ordena la lista solo por servidor
            elif favorite_priority == 1:
                autoplay_list.sort(key=lambda priority: priority[0])

            # Se ordena la lista por servidor y calidad
            elif favorite_priority == 0:
                autoplay_list.sort(key=lambda priority: priority[2])
                ordered_list = sorted(autoplay_list, key=lambda priority: priority[0])
                autoplay_list = ordered_list

            #logger.debug('autoplay_list: ' + str(autoplay_list) + ' favorite priority: ' + str(favorite_priority))

            # Si hay elementos en la lista de autoplay se intenta reproducir cada elemento, hasta encontrar uno
            # funcional
            # o fallen todos
            if autoplay_list:
                played = False
                max_intentos = 5 # TODO: Este numero podria ser configurable
                max_intentos_servers = {}

                # Si se esta reproduciendo algo detiene la reproduccion
                if platformtools.is_playing():
                    platformtools.stop_video()
                for indice in autoplay_list:
                    if not platformtools.is_playing() and not played:
                        videoitem = indice[1]

                        if not videoitem.server in max_intentos_servers:
                            max_intentos_servers[videoitem.server] = max_intentos

                        # Si se han alcanzado el numero maximo de intentos de este servidor saltamos al siguiente
                        if max_intentos_servers[videoitem.server] == 0:
                            continue

                        #logger.debug('item.language: ' + videoitem.language)
                        lang = " "
                        if hasattr(videoitem, 'language') and videoitem.language != "":
                            lang = " '%s' " % videoitem.language

                        platformtools.dialog_notification("AutoPlay iniciado en:", "%s%s%s" % (
                        videoitem.server.upper(), lang, indice[3].upper()), sound=False)

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

            # devuelve la lista de enlaces para la eleccion manual
            config.set_setting("default_action", user_config_setting)
        return itemlist


def prepare_autoplay_settings (channel, list_servers, list_quality):
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
    priority_list = ['Servidor y Calidad', 'Servidor', 'Calidad']
    list_language = get_languages(channel)

    # Se obtiene el nodo autoplay desde el json
    autoplay_node = filetools.get_node_from_data_json(fname, "AUTOPLAY")

    # Se Obtiene el nodo del canal desde el json
    channel_node = autoplay_node.get(channel, {})

    # Si el nodo esta vacio lo crea
    if len(channel_node) == 0:
        channel_settings = {
                            "servers": list(valid_servers),
                            "quality": list(valid_quality),
                            "priority": priority_list,
                            "settings": {
                                         "active": False,
                                         "custom": False,
                                         "language": 0,
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


def check_value (channel, value, value_type):
    ''' comprueba la existencia de un valor en la lista de servidores o calidades
        si no eixtirera los agrerga a la lista en el json

    :param channel: str
    :param value: str (un servidor o calidad)
    :param value_type: str (server o quality)
    :return: list
    '''
    logger.info()
    fname = 'autoplay'

    autoplay_node = filetools.get_node_from_data_json(fname, 'AUTOPLAY')
    value_list = autoplay_node.get(channel, {}).get(value_type, [])

    if len(value_list) == 0 or (value != '' and value not in value_list):
        value_list.append(value)
        fname, json_data = filetools.update_json_data(autoplay_node, fname, 'AUTOPLAY')
        result = filetools.write(fname, json_data)

    return value_list


def autoplay_config (item):

    logger.info()

    fname = 'autoplay'
    # Obtenemos los datos de json
    autoplay_node = filetools.get_node_from_data_json(fname, 'AUTOPLAY')
    channel_node = autoplay_node.get(item.from_channel, {})
    settings_config = channel_node.get('settings', {})

    allow_option = True
    active = settings_config.get('active', False)
    #logger.debug('active: ' + str(active))

    list_controls = []

    active_settings = {"id": "active",
                       "label": "AutoPlay (activar/desactivar la auto-reproduccion)",
                       "color": "0xffffff99",
                       "type": "bool",
                       "default": active,
                       "enabled": allow_option,
                       "visible": allow_option
                      }
    list_controls.append(active_settings)


    list_language = get_languages(item.from_channel)
    channel_config = filetools.get_node_from_data_json(item.from_channel, 'settings')
    status_language = channel_config.get("filter_languages", 0)

    set_language = {"id": "language",
                    "label": "Idioma para AutoPlay (Obligatorio)",
                    "color": "0xffffff99",
                    "type": "list",
                    "default": status_language,
                    "enabled": "eq(-1,true)",
                    "visible": True,
                    "lvalues": list_language
                    }

    list_controls.append(set_language)

    separador = {"id": "label",
                 "label": "         "
                          "_________________________________________________________________________________________",
                 "type": "label",
                 "enabled": True,
                 "visible": True
                 }
    list_controls.append(separador)

    custom_status = settings_config.get('custom', False)
    #logger.debug('custom_status: ' + str(custom_status))
    custom_settings = {"id": "custom",
                       "label": "   Personalizar Preferidos (Opcional)", "color": "0xff66ffcc",
                       "type": "bool",
                       "default": custom_status,
                       "enabled": "eq(-3,true)",
                       "visible": True
                      }
    list_controls.append(custom_settings)

    priority_list = channel_node.get("priority", [])
    status_priority = channel_node.get("settings", {}).get("priority", 0)

    set_priority = {"id": "priority",
                    "label": "      - Prioridad (Indica el orden para Auto-Reproducir)",
                    "color": "0xffffff99",
                    "type": "list", "default": status_priority,
                    "enabled": "eq(-4,true)+eq(-1,true)",
                    "visible": True,
                    "lvalues": priority_list
                   }
    list_controls.append(set_priority)

    server_list = channel_node.get("servers", [])
    for num in range(1, 4):
        pos1 = num + 4
        pos2 = num + 1
        status_server = channel_node.get("settings", {}).get("server_%s" % num, 0)

        set_servers = {"id": "server_%s" % num,
                       "label": u"      \u2665 Servidor Favorito %s" % num,
                       "color": "0xfffcab14",
                       "type": "list", "default": status_server,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, pos2),
                       "visible": True, "lvalues": server_list
                      }
        list_controls.append(set_servers)

    quality_list = channel_node.get("quality", [])
    for num in range(1, 4):
        pos1 = num + 7
        pos2 = num + 4
        status_quality = channel_node.get("settings", {}).get("quality_%s" % num, 0)

        set_quality = {"id": "quality_%s" % num,
                       "label": u"      \u2665 Calidad Favorita %s" % num,
                       "color": "0xfff442d9",
                       "type": "list",
                       "default": status_quality,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, pos2),
                       "visible": True,
                       "lvalues": quality_list
                      }
        list_controls.append(set_quality)

    platformtools.show_channel_settings(list_controls=list_controls, callback='save', item=item, caption='AutoPlay')


def save (dict_data_saved, item):
    '''
    Guarda los datos de la ventana de configuracion

    :param dict_data_saved: dict
    :param item: item
    :return:
    '''
    logger.info()
    channel = dict_data_saved.from_channel
    fname = 'autoplay'

    autoplay_node = filetools.get_node_from_data_json(fname, 'AUTOPLAY')
    channel_config = filetools.get_node_from_data_json(channel, 'settings')
    channel_node = autoplay_node.get(channel, {})
    settings_node = channel_node.get('settings', {})

    new_channel_settings = item

    #logger.debug("settings_node['active']: " + str(settings_node['active']))
    channel_node['settings'] = new_channel_settings
    #logger.debug("settings_node['custom']: " + str(settings_node['custom']))
    channel_node['settings'] = new_channel_settings
    fname, json_data = filetools.update_json_data(autoplay_node, fname, 'AUTOPLAY')
    result = filetools.write(fname, json_data)

    channel_config['filter_languages'] = new_channel_settings['language']
    fname, json_data = filetools.update_json_data(channel_config, channel, 'settings')
    result = filetools.write(fname, json_data)


# Metodo auxiliar genera las listas de servidores y calidades an base al un itemlist y patron(calidad) recibido

def make_server_list (itemlist):
    '''

    :param itemlist: list (lista de elementos que contenga el nombre del servidor)
    :return: log con una lista de servidores
    '''
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


def get_languages (channel):
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

def check_status (channel):

    logger.info()

    fname = 'autoplay'
    # Obtenemos el estado de AutoPlay desde el json
    autoplay_node = filetools.get_node_from_data_json(fname, 'AUTOPLAY')
    channel_node = autoplay_node.get(channel, {})
    settings_node = channel_node.get('settings', {})
    result = settings_node.get('active', False)
    return result

