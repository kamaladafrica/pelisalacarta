# -*- coding: utf-8 -*-
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
# ------------------------------------------------------------
# platformtools
# ------------------------------------------------------------
# Herramientas responsables de adaptar los diferentes 
# cuadros de dialogo a una plataforma en concreto,
# en este caso Kodi.
# version 2.0
# ------------------------------------------------------------

import os
import sys
import urllib

import xbmc
import xbmcgui
import xbmcplugin
from core import config
from core import logger
from core.item import Item

DEBUG = config.get_setting("debug")


def dialog_ok(heading, line1, line2="", line3=""):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, line1, line2, line3)


def dialog_notification(heading, message, icon=0, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    l_icono = xbmcgui.NOTIFICATION_INFO, xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR
    dialog.notification(heading, message, l_icono[icon], time, sound)


def dialog_yesno(heading, line1, line2="", line3="", nolabel="No", yeslabel="Si", autoclose=""):
    dialog = xbmcgui.Dialog()
    if autoclose:
        return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel, autoclose)
    else:
        return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)


def dialog_select(heading, _list):
    return xbmcgui.Dialog().select(heading, _list)


def dialog_progress(heading, line1, line2="", line3=""):
    dialog = xbmcgui.DialogProgress()
    dialog.create(heading, line1, line2, line3)
    return dialog


def dialog_progress_bg(heading, message=""):
    dialog = xbmcgui.DialogProgressBG()
    dialog.create(heading, message)
    return dialog


def dialog_input(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return None


def dialog_numeric(_type, heading, default=""):
    dialog = xbmcgui.Dialog()
    dialog.numeric(_type, heading, default)
    return dialog


def itemlist_refresh():
    xbmc.executebuiltin("Container.Refresh")


def itemlist_update(item):
    xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")


def render_items(itemlist, parent_item):
    """
    Función encargada de mostrar el itemlist en kodi, se pasa como parametros el itemlist y el item del que procede
    @type itemlist: list
    @param itemlist: lista de elementos a mostrar

    @type parent_item: item
    @param parent_item: elemento padre
    """
    # Si el itemlist no es un list salimos
    if not type(itemlist) == list:
        return

    # Si no hay ningun item, mostramos un aviso
    if not len(itemlist):
        itemlist.append(Item(title="No hay elementos que mostrar"))

    # Recorremos el itemlist
    for item in itemlist:

        # Si el item no contiene categoria,le ponemos la del item padre
        if item.category == "":
            item.category = parent_item.category

        # Si el item no contiene fanart,le ponemos la del item padre
        if item.fanart == "":
            item.fanart = parent_item.fanart

        # Formatear titulo
        if item.text_color:
            item.title = '[COLOR %s]%s[/COLOR]' % (item.text_color, item.title)
        if item.text_blod:
            item.title = '[B]%s[/B]' % item.title
        if item.text_italic:
            item.title = '[I]%s[/I]' % item.title

        # IconImage para folder y video
        if item.folder:
            icon_image = "DefaultFolder.png"
        else:
            icon_image = "DefaultVideo.png"

        # Creamos el listitem
        listitem = xbmcgui.ListItem(item.title, iconImage=icon_image, thumbnailImage=item.thumbnail)

        # Ponemos el fanart
        listitem.setProperty('fanart_image',
                             item.fanart if item.fanart else os.path.join(config.get_runtime_path(), "fanart.jpg"))

        # TODO: ¿Se puede eliminar esta linea? yo no he visto que haga ningun efecto.
        xbmcplugin.setPluginFanart(int(sys.argv[1]), os.path.join(config.get_runtime_path(), "fanart.jpg"))

        # Añadimos los infoLabels
        set_infolabels(listitem, item)

        # Montamos el menu contextual
        context_commands = set_context_commands(item, parent_item)

        # Añadimos el item
        if config.get_platform() == "boxee":
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url='%s?%s' % (sys.argv[0], item.tourl()),
                                        listitem=listitem, isFolder=item.folder)
        else:
            listitem.addContextMenuItems(context_commands, replaceItems=True)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url='%s?%s' % (sys.argv[0], item.tourl()),
                                        listitem=listitem, isFolder=item.folder,
                                        totalItems=item.totalItems if item.totalItems else 0)

    # Vista 5x3 hasta llegar al listado de canales
    if parent_item.channel not in ["channelselector", ""]:
        xbmcplugin.setContent(int(sys.argv[1]), "movies")

    # TODO: ¿Que utlilidad tiene esta linea?
    xbmcplugin.setPluginCategory(handle=int(sys.argv[1]), category=parent_item.category)

    # No ordenar items
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)

    # Viewmodes:
    # Creo que es mas lógico que al item se le especifique que vista tendra al abrirlo.
    # El cambio puede provocar que algun canal no muestre los items en la vista deseada, pero es mejor ir corrigiendolo
    # que arrastrar algo que no tiene sentido
    if config.get_setting("forceview") == "true":
        if parent_item.viewmode == "list":
            xbmc.executebuiltin("Container.SetViewMode(50)")
        elif parent_item.viewmode == "movie_with_plot":
            xbmc.executebuiltin("Container.SetViewMode(503)")
        elif parent_item.viewmode == "movie":
            xbmc.executebuiltin("Container.SetViewMode(500)")

    # Cerramos el directorio
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)


def set_infolabels(listitem, item):
    """
    Metodo para pasar la informacion al listitem (ver tmdb.set_InfoLabels() )
    item.infoLabels es un dicionario con los pares de clave/valor descritos en:
    http://mirrors.xbmc.org/docs/python-docs/14.x-helix/xbmcgui.html#ListItem-setInfo
    @param listitem: objeto xbmcgui.ListItem
    @type listitem: xbmcgui.ListItem
    @param item: objeto Item que representa a una pelicula, serie o capitulo
    @type item: item
    """

    listitem.setInfo("video", item.infoLabels)
    listitem.setInfo("video", {"Title": item.title})


def set_context_commands(item, parent_item):
    """
    Función para generar los menus contextuales.
        1. Partiendo de los datos de item.context
             a. Metodo antiguo item.context tipo str separando las opciones por "|" (ejemplo: item.context = "1|2|3")
                (solo predefinidos)
            b. Metodo list: item.context es un list con las diferentes opciones del menu:
                - Predefinidos: Se cargara una opcion predefinida con un nombre.
                    item.context = ["1","2","3"]

                - dict(): Se cargara el item actual modificando los campos que se incluyan en el dict() en caso de
                    modificar los campos channel y action estos serán guardados en from_channel y from_action.
                    item.context = [{"title":"Nombre del menu", "action": "action del menu", "channel",
                                    "channel del menu"}, {...}]

                - Item(): Se cargara el item pasado como opcion en item.context, tal cual se pase
                    item.context = [Item(title="titulo del menu", action="action del menu", channel="channel de menu"),
                                    Item(...)]
        2. Añadiendo opciones segun criterios
            Se pueden añadir opciones al menu contextual a items que cumplan ciertas condiciones

        3. Añadiendo opciones a todos los items
            Se pueden añadir opciones al menu contextual para todos los items

    @param item: elemento que contiene los menu contextuales
    @type item: item
    @param parent_item:
    @type parent_item: item
    """
    context_commands = []

    # Creamos un list con las diferentes opciones incluidas en item.context
    if type(item.context) == str:
        context = item.context.split("|")
    elif type(item.context) == list:
        context = item.context
    else:
        context = []

    # Eliminamos los datos de item.context, ya que no los vamos a necesitar mas
    item.context = ""

    # Opciones segun item.context
    for command in context:
        # Predefinidos
        if type(command) == str:
            if command == "menu filtro":
                context_commands.append(("Menu Filtro", "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], item.clone(
                    channel="filtertools",
                    action="config_filter",
                    from_channel=item.channel
                ).tourl())))

            if command == "guardar filtro":
                context_commands.append(("guardar filtro serie", "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], item.clone(
                    channel="filtertools",
                    action="save_filter",
                    from_channel=item.channel
                ).tourl())))

            if command == "borrar filtro":
                context_commands.append(("Eliminar Filtro", "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], item.clone(
                    channel="filtertools",
                    action="del_filter",
                    from_channel=item.channel
                ).tourl())))

        # Formato dict
        if type(command) == dict:
            # Los parametros del dict, se sobreescriben al nuevo context_item en caso de sobreescribir "action" y
            # "channel", los datos originales se guardan en "from_action" y "from_channel"
            if "action" in command:
                command["from_action"] = item.action
            if "channel" in command:
                command["from_channel"] = item.channel
            context_commands.append(
                (command["title"], "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], item.clone(**command).tourl())))

        # Formato Item
        if type(command) == Item:
            context_commands.append((command.title, "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], command.tourl())))

    # Opciones segun criterios
    # Quitar de Favoritos
    if parent_item.channel == "favoritos":
        context_commands.append(("Quitar a Favoritos", "XBMC.RunPlugin(%s?%s)" %
                                 (sys.argv[0], item.clone(channel="favoritos", action="deletebookmark").tourl())))

    # Añadir a Favoritos
    if item.channel not in ["channelselector", "favoritos", "descargas", "buscador", "biblioteca", "novedades", "ayuda",
                            "configuracion", ""] and not parent_item.channel == "favoritos":
        context_commands.append(("Añadir a Favoritos", "XBMC.RunPlugin(%s?%s)" %
                                 (sys.argv[0], item.clone(channel="favoritos", action="savebookmark",
                                                          from_channel=item.channel, from_action=item.action).tourl())))

    # Añadimos opción contextual para Añadir la serie completa a la biblioteca
    if item.action in ["episodios", "get_episodios"] and (item.contentSerieName or item.show):
        context_commands.append(("Añadir Serie a Biblioteca", "XBMC.RunPlugin(%s?%s)" %
                                 (sys.argv[0], item.clone(action="add_serie_to_library",
                                                          from_action=item.action).tourl())))

    # Añadir Pelicula a Biblioteca
    if item.action in ["detail", "findvideos"] and not (item.contentSerieName or item.show):
        context_commands.append(("Añadir Pelicula a Biblioteca", "XBMC.RunPlugin(%s?%s)" %
                                 (sys.argv[0], item.clone(action="add_pelicula_to_library",
                                                          from_action=item.action).tourl())))

    # Descargar pelicula
    if item.action in ["detail", "findvideos"] and not (item.contentSerieName or item.show):
        context_commands.append(("Descargar Pelicula", "XBMC.RunPlugin(%s?%s)" %
                                 (sys.argv[0], item.clone(channel="descargas", action="save_download_movie",
                                                          from_channel=item.channel, from_action=item.action).tourl())))

    # Descargar serie
    if item.action in ["episodios", "get_episodios"] and (item.contentSerieName or item.show):
        context_commands.append(("Descargar Serie", "XBMC.RunPlugin(%s?%s)" %
                                 (sys.argv[0], item.clone(channel="descargas", action="save_download_tvshow",
                                                          from_channel=item.channel, from_action=item.action).tourl())))

    # Descargar episodio
    if item.action in ["detail", "findvideos"] and (item.contentSerieName or item.show):
        context_commands.append(("Descargar Episodio", "XBMC.RunPlugin(%s?%s)" %
                                 (sys.argv[0], item.clone(channel="descargas", action="save_download",
                                                          from_channel=item.channel, from_action=item.action).tourl())))

    # Opciones para todos los items
    # Abrir configuración desde cualquier lugar
    context_commands.append(("Abrir Configuración", "XBMC.RunPlugin(%s?%s)" %
                             (sys.argv[0], Item(channel="configuracion", action="mainlist").tourl())))

    return context_commands


def is_playing():
    return xbmc.Player().isPlaying()


def play_video(item, strm=False):
    logger.info("pelisalacarta.platformcode.platformtools play_video")
    # logger.info(item.tostring('\n'))

    default_action = config.get_setting("default_action")
    logger.info("default_action="+default_action)

    # Abre el diálogo de selección para ver las opciones disponibles
    opciones, video_urls, seleccion, salir = get_dialogo_opciones(item, default_action, strm)
    if salir:
        return

    # se obtienen la opción predeterminada de la configuración del addon
    seleccion = get_seleccion(default_action, opciones, seleccion, video_urls)

    logger.info("seleccion=%d" % seleccion)
    logger.info("seleccion=%s" % opciones[seleccion])

    # se ejecuta la opcion disponible, jdwonloader, descarga, favoritos, añadir a la biblioteca... SI NO ES PLAY
    salir = set_opcion(item, seleccion, opciones, video_urls)
    if salir:
        return

    # obtenemos el video seleccionado
    mediaurl, view = get_video_seleccionado(item, seleccion, video_urls)
    if mediaurl == "":
        return

    # se obtiene la información del video.
    xlistitem = get_info_video(item, mediaurl, strm)

    # se lanza el reproductor
    set_player(item, xlistitem, mediaurl, view, strm)


def get_info_video(item, mediaurl, strm):
    logger.info("pelisalacarta.platformcode.platformtools get_info_video")
    # Obtención datos de la Biblioteca (solo strms que estén en la biblioteca)
    if strm:
        xlistitem = get_library_info(mediaurl)
    else:
        play_title = item.fulltitle
        play_thumbnail = item.thumbnail
        play_plot = item.plot

        if item.hasContentDetails == "true":
            play_title = item.contentTitle
            play_thumbnail = item.contentThumbnail
            play_plot = item.contentPlot

        try:
            xlistitem = xbmcgui.ListItem(play_title, iconImage="DefaultVideo.png", thumbnailImage=play_thumbnail,
                                         path=mediaurl)
        except:
            xlistitem = xbmcgui.ListItem(play_title, iconImage="DefaultVideo.png", thumbnailImage=play_thumbnail)

        xlistitem.setInfo("video", {"Title": play_title, "Plot": play_plot, "Studio": item.channel,
                                    "Genre": item.category})

        set_infolabels(xlistitem, item)

    return xlistitem


def get_seleccion(default_action, opciones, seleccion, video_urls):
    # preguntar
    if default_action == "0":
        # "Elige una opción"
        seleccion = dialog_select(config.get_localized_string(30163), opciones)
    # Ver en calidad baja
    elif default_action == "1":
        seleccion = 0
    # Ver en alta calidad
    elif default_action == "2":
        seleccion = len(video_urls) - 1
    # jdownloader
    elif default_action == "3":
        seleccion = seleccion
    else:
        seleccion = 0
    return seleccion


def show_channel_settings(list_controls=None, dict_values=None, caption="", callback=None, item=None,
                          custom_button=None):
    """
    Muestra un cuadro de configuracion personalizado para cada canal y guarda los datos al cerrarlo.
    
    Parametros: ver descripcion en xbmc_config_menu.SettingsWindow
    @param list_controls: lista de elementos a mostrar en la ventana.
    @type list_controls: list
    @param dict_values: valores que tienen la lista de elementos.
    @type dict_values: dict
    @param caption: titulo de la ventana
    @type caption: str
    @param callback: función que se llama tras cerrarse la ventana.
    @type callback: str
    @param item: item para el que se muestra la ventana de configuración.
    @type item: Item
    @param custom_button: botón personalizado, que se muestra junto a "OK" y "Cancelar".
    @type custom_button: dict

    @return: devuelve la ventana con los elementos
    @rtype: SettingsWindow
    """
    from xbmc_config_menu import SettingsWindow
    return SettingsWindow("ChannelSettings.xml", config.get_runtime_path())\
        .start(list_controls=list_controls, dict_values=dict_values, title=caption, callback=callback, item=item,
               custom_button=custom_button)


def show_video_info(data, caption="", callback=None, item=None):
    """
    Muestra una ventana con la info del vídeo. Opcionalmente se puede indicar el titulo de la ventana mendiante
    el argumento 'caption'.

    Si se pasa un item como argumento 'data' usa el scrapper Tmdb para buscar la info del vídeo
        En caso de peliculas:
            Coge el titulo de los siguientes campos (en este orden)
                  1. contentTitle (este tiene prioridad 1)
                  2. fulltitle (este tiene prioridad 2)
                  3. title (este tiene prioridad 3)
            El primero que contenga "algo" lo interpreta como el titulo (es importante asegurarse que el titulo este en
            su sitio)

        En caso de series:
            1. Busca la temporada y episodio en los campos contentSeason y contentEpisodeNumber
            2. Intenta Sacarlo del titulo del video (formato: 1x01)

            Aqui hay dos opciones posibles:
                  1. Tenemos Temporada y episodio
                    Muestra la información del capitulo concreto
                    Se puede navegar con las flechas para cambiar de temporada / eìsodio
                    Flecha Arriba: Aumentar temporada
                    Flecha Abajo: Disminuir temporada
                    Flecha Derecha: Aumentar eìsodio
                    Flecha Izquierda: Disminuir eìsodio
                  2. NO Tenemos Temporada y episodio
                    En este caso muestra la informacion generica de la serie

    Si se pasa como argumento 'data' un dict() muestra en la ventana directamente la información pasada (sin usar el
    scrapper)
        Formato:
            En caso de peliculas:
                dict({
                         "type"           : "movie",
                         "title"          : "Titulo de la pelicula",
                         "original_title" : "Titulo original de la pelicula",
                         "date"           : "Fecha de lanzamiento",
                         "language"       : "Idioma original de la pelicula",
                         "rating"         : "Puntuacion de la pelicula",
                         "genres"         : "Generos de la pelicula",
                         "thumbnail"      : "Ruta para el thumbnail",
                         "fanart"         : "Ruta para el fanart",
                         "overview"       : "Sinopsis de la pelicula"
                      }
            En caso de series:
                dict({
                         "type"           : "tv",
                         "title"          : "Titulo de la serie",
                         "episode_title"  : "Titulo del episodio",
                         "date"           : "Fecha de emision",
                         "language"       : "Idioma original de la serie",
                         "rating"         : "Puntuacion de la serie",
                         "genres"         : "Generos de la serie",
                         "thumbnail"      : "Ruta para el thumbnail",
                         "fanart"         : "Ruta para el fanart",
                         "overview"       : "Sinopsis de la del episodio o de la serie",
                         "seasons"        : "Numero de Temporadas",
                         "season"         : "Temporada",
                         "episodes"       : "Numero de episodios de la temporada",
                         "episode"        : "Episodio"
                      }
    Si se pasa como argumento 'data' un listado de dict() con la estructura anterior, muestra los botones 'Anterior' y
    'Siguiente' para ir recorriendo la lista. Ademas muestra los botones 'Aceptar' y 'Cancelar' que llamaran a la
    funcion 'callback' del canal desde donde se realiza la llamada pasandole como parametros el elemento actual (dict())
    o None respectivamente.

    @param data: información para obtener datos del scraper.
    @type data: item, dict, list(dict)
    @param caption: titulo de la ventana.
    @type caption: str
    @param callback: función que se llama después de cerrarse la ventana de información
    @type callback: str
    @param item: elemento del que se va a mostrar la ventana de información
    @type item: Item
    """

    from xbmc_info_window import InfoWindow
    return InfoWindow("InfoWindow.xml", config.get_runtime_path()).Start(data, caption=caption, callback=callback,
                                                                         item=item)


def alert_no_disponible_server(server):
    # 'El vídeo ya no está en %s' , 'Prueba en otro servidor o en otro canal'
    dialog_ok(config.get_localized_string(30055), (config.get_localized_string(30057) % server),
              config.get_localized_string(30058))


def alert_unsopported_server():
    # 'Servidor no soportado o desconocido' , 'Prueba en otro servidor o en otro canal'
    dialog_ok(config.get_localized_string(30065), config.get_localized_string(30058))


def get_library_info(mediaurl):
    """
    Obtiene información de la Biblioteca si existe (ficheros strm) o de los parámetros
    @type mediaurl: str
    @param mediaurl: url a la que se asocia la información de la biblioteca
    """
    if DEBUG:
        logger.info('pelisalacarta.platformcode.platformstools playlist OBTENCIÓN DE DATOS DE BIBLIOTECA')

    # Información básica
    label = xbmc.getInfoLabel('listitem.label')
    label2 = xbmc.getInfoLabel('listitem.label2')
    icon_image = xbmc.getInfoImage('listitem.icon')
    thumbnail_image = xbmc.getInfoImage('listitem.Thumb')

    if DEBUG:
        logger.info("[platformstools.py]getMediaInfo: label = " + label)
        logger.info("[platformstools.py]getMediaInfo: label2 = " + label2)
        logger.info("[platformstools.py]getMediaInfo: iconImage = " + icon_image)
        logger.info("[platformstools.py]getMediaInfo: thumbnailImage = " + thumbnail_image)

    # Creación de listitem
    listitem = xbmcgui.ListItem(label, label2, icon_image, thumbnail_image, mediaurl)

    # Información adicional
    lista = [
        # (Comedy)
        ('listitem.genre', 's'),
        # (2009)
        ('listitem.year', 'i'),
        # (4)
        ('listitem.episode', 'i'),
        # (1)
        ('listitem.season', 'i'),
        # (192)
        ('listitem.top250', 'i'),
        # (3)
        ('listitem.tracknumber', 'i'),
        # (6.4) - range is 0..10
        ('listitem.rating', 'f'),
        # (2) - number of times this item has been played
        ('listitem.playcount', 'i'),
        # (2) - range is 0..8.  See GUIListItem.h for values
        # ('listitem.overlay', 'i'),
        # JUR - listitem devuelve un string, pero addinfo espera un int. Ver traducción más abajo
        ('listitem.overlay', 's'),
        # (Michal C. Hall) - List concatenated into a string
        # ('listitem.cast', 's'),
        # (Michael C. Hall|Dexter) - List concatenated into a string
        # ('listitem.castandrole', 's'),
        # (Dagur Kari)
        ('listitem.director', 's'),
        # (PG-13)
        ('listitem.mpaa', 's'),
        # (Long Description)
        ('listitem.plot', 's'),
        # (Short Description)
        ('listitem.plotoutline', 's'),
        # (Big Fan)
        ('listitem.title', 's'),
        # (3)
        ('listitem.duration', 's'),
        # (Warner Bros.)
        ('listitem.studio', 's'),
        # (An awesome movie) - short description of movie
        ('listitem.tagline', 's'),
        # (Robert D. Siegel)
        ('listitem.writer', 's'),
        # (Heroes)
        ('listitem.tvshowtitle', 's'),
        # (2005-03-04)
        ('listitem.premiered', 's'),
        # (Continuing) - status of a TVshow
        ('listitem.status', 's'),
        # (tt0110293) - IMDb code
        ('listitem.code', 's'),
        # (2008-12-07)
        ('listitem.aired', 's'),
        # (Andy Kaufman) - writing credits
        ('listitem.credits', 's'),
        # (%Y-%m-%d %h
        ('listitem.lastplayed', 's'),
        # (The Joshua Tree)
        ('listitem.album', 's'),
        # (12345 votes)
        ('listitem.votes', 's'),
        # (/home/user/trailer.avi)
        ('listitem.trailer', 's'),
    ]
    # Obtenemos toda la info disponible y la metemos en un diccionario
    # para la función setInfo.
    infodict = dict()
    for label, tipo in lista:
        key = label.split('.', 1)[1]
        value = xbmc.getInfoLabel(label)
        if value != "":
            if DEBUG:
                logger.info("[platformstools.py]getMediaInfo: "+key+" = " + value)
            if tipo == 's':
                infodict[key] = value
            elif tipo == 'i':
                infodict[key] = int(value)
            elif tipo == 'f':
                infodict[key] = float(value)

    # Transforma el valor de overlay de string a int.
    if 'overlay' in infodict:
        value = infodict['overlay'].lower()
        if value.find('rar') > -1:
            infodict['overlay'] = 1
        elif value.find('zip') > -1:
            infodict['overlay'] = 2
        elif value.find('trained') > -1:
            infodict['overlay'] = 3
        elif value.find('hastrainer') > -1:
            infodict['overlay'] = 4
        elif value.find('locked') > -1:
            infodict['overlay'] = 5
        elif value.find('unwatched') > -1:
            infodict['overlay'] = 6
        elif value.find('watched') > -1:
            infodict['overlay'] = 7
        elif value.find('hd') > -1:
            infodict['overlay'] = 8
        else:
            infodict.pop('overlay')
    if len(infodict) > 0:
        listitem.setInfo("video", infodict)

    return listitem


def handle_wait(time_to_wait, title, text):
    logger.info("handle_wait(time_to_wait=%d)" % time_to_wait)
    espera = dialog_progress(' '+title, "")

    secs = 0
    increment = int(100 / time_to_wait)

    cancelled = False
    while secs < time_to_wait:
        secs += 1
        percent = increment*secs
        secs_left = str((time_to_wait - secs))
        remaining_display = ' Espera '+secs_left+' segundos para que comience el vídeo...'
        espera.update(percent, ' '+text, remaining_display)
        xbmc.sleep(1000)
        if espera.iscanceled():
            cancelled = True
            break

    if cancelled:
        logger.info('Espera cancelada')
        return False
    else:
        logger.info('Espera finalizada')
        return True


def get_dialogo_opciones(item, default_action, strm):
    logger.info("platformtools get_dialogo_opciones")
    from core import servertools

    opciones = []
    error = False

    try:
        item.server = item.server.lower()
    except AttributeError:
        item.server = ""

    if item.server == "":
        item.server = "directo"

    # Si no es el modo normal, no muestra el diálogo porque cuelga XBMC
    muestra_dialogo = (config.get_setting("player_mode") == "0" and not strm)

    # Extrae las URL de los vídeos, y si no puedes verlo te dice el motivo
    video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(
        item.server, item.url, item.password, muestra_dialogo)

    seleccion = 0
    # Si puedes ver el vídeo, presenta las opciones
    if puedes:
        for video_url in video_urls:
            opciones.append(config.get_localized_string(30151) + " " + video_url[0])

        if item.server == "local":
            opciones.append(config.get_localized_string(30164))
        else:
            # "Descargar"
            opcion = config.get_localized_string(30153)
            opciones.append(opcion)

            if item.channel == "favoritos":
                # "Quitar de favoritos"
                opciones.append(config.get_localized_string(30154))
            else:
                # "Añadir a favoritos"
                opciones.append(config.get_localized_string(30155))

            if not strm:
                # "Añadir a Biblioteca"
                opciones.append(config.get_localized_string(30161))

            if config.get_setting("jdownloader_enabled") == "true":
                # "Enviar a JDownloader"
                opciones.append(config.get_localized_string(30158))

        if default_action == "3":
            seleccion = len(opciones)-1

        # Busqueda de trailers en youtube
        if item.channel not in ["Trailer", "ecarteleratrailers"]:
            # "Buscar Trailer"
            opciones.append(config.get_localized_string(30162))

    # Si no puedes ver el vídeo te informa
    else:
        if item.server != "":
            if "<br/>" in motivo:
                dialog_ok("No puedes ver ese vídeo porque...", motivo.split("<br/>")[0], motivo.split("<br/>")[1],
                          item.url)
            else:
                dialog_ok("No puedes ver ese vídeo porque...", motivo, item.url)
        else:
            dialog_ok("No puedes ver ese vídeo porque...", "El servidor donde está alojado no está",
                      "soportado en pelisalacarta todavía", item.url)

        if item.channel == "favoritos":
            # "Quitar de favoritos"
            opciones.append(config.get_localized_string(30154))

        if len(opciones) == 0:
            error = True

    return opciones, video_urls, seleccion, error


def set_opcion(item, seleccion, opciones, video_urls):
    logger.info("platformtools set_opcion")
    salir = False
    # No ha elegido nada, lo más probable porque haya dado al ESC
    # TODO revisar
    if seleccion == -1:
        # Para evitar el error "Uno o más elementos fallaron" al cancelar la selección desde fichero strm
        listitem = xbmcgui.ListItem(item.title, iconImage="DefaultVideo.png", thumbnailImage=item.thumbnail)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, listitem)

    # "Enviar a JDownloader"
    if opciones[seleccion] == config.get_localized_string(30158):
        from core import scrapertools

        # TODO comprobar que devuelve 'data'
        if item.subtitle != "":
            data = scrapertools.cachePage(config.get_setting("jdownloader")+"/action/add/links/grabber0/start1/web=" +
                                          item.url + " " + item.thumbnail + " " + item.subtitle)
        else:
            data = scrapertools.cachePage(config.get_setting("jdownloader")+"/action/add/links/grabber0/start1/web=" +
                                          item.url + " " + item.thumbnail)
        salir = True

    # "Enviar a pyLoad"
    elif opciones[seleccion] == config.get_localized_string(30158).replace("jDownloader", "pyLoad"):
        logger.info("Enviando a pyload...")

        if item.show != "":
            package_name = item.show
        else:
            package_name = "pelisalacarta"

        from core import pyload_client
        pyload_client.download(url=item.url, package_name=package_name)
        salir = True

    # "Descargar"
    elif opciones[seleccion] == config.get_localized_string(30153):
        item.video_urls = video_urls
        from channels import descargas
        descargas.save_download_movie(item)
        salir = True

    # "Quitar de favoritos"
    elif opciones[seleccion] == config.get_localized_string(30154):
        from channels import favoritos
        favoritos.deletebookmark(item)

        # 'Se ha quitado de favoritos'
        dialog_ok(config.get_localized_string(30102), item.title, config.get_localized_string(30105))
        xbmc.executebuiltin("Container.Refresh")
        salir = True

    # "Añadir a favoritos":
    elif opciones[seleccion] == config.get_localized_string(30155):
        from channels import favoritos
        favoritos.savebookmark(item)
        salir = True

    # "Añadir a Biblioteca":  # Library
    elif opciones[seleccion] == config.get_localized_string(30161):

        titulo = item.fulltitle
        if titulo == "":
            titulo = item.title

        # TODO ¿SOLO peliculas?
        new_item = item.clone(title=titulo, action="play_from_library", category="Cine",
                              fulltitle=item.fulltitle, channel=item.channel)
        from platformcode import library
        insertados, sobreescritos, fallidos = library.save_library_movie(new_item)

        advertencia = xbmcgui.Dialog()
        if fallidos == 0:
            advertencia.ok(config.get_localized_string(30131), titulo,
                           config.get_localized_string(30135))  # 'se ha añadido a la biblioteca'

        salir = True

    # "Buscar Trailer":
    elif opciones[seleccion] == config.get_localized_string(30162):
        config.set_setting("subtitulo", "false")
        xbmc.executebuiltin("XBMC.RunPlugin(%s?%s)" %
                            (sys.argv[0], item.clone(channel="trailertools", action="buscartrailer",
                                                     contextual=True).tourl()))
        salir = True

    return salir


def get_video_seleccionado(item, seleccion, video_urls):
    logger.info("platformtools get_video_seleccionado")
    mediaurl = ""
    view = False
    wait_time = 0

    # Ha elegido uno de los vídeos
    if seleccion < len(video_urls):
        mediaurl = video_urls[seleccion][1]
        if len(video_urls[seleccion]) > 3:
            wait_time = video_urls[seleccion][2]
            item.subtitle = video_urls[seleccion][3]
        elif len(video_urls[seleccion]) > 2:
            wait_time = video_urls[seleccion][2]
        view = True

    # Si no hay mediaurl es porque el vídeo no está :)
    logger.info("pelisalacarta.platformcode.platformstools mediaurl=" + mediaurl)
    if mediaurl == "":
        if item.server == "unknown":
            alert_unsopported_server()
        else:
            alert_no_disponible_server(item.server)

    # Si hay un tiempo de espera (como en megaupload), lo impone ahora
    if wait_time > 0:
        continuar = handle_wait(wait_time, item.server, "Cargando vídeo...")
        if not continuar:
            mediaurl = ""

    return mediaurl, view


def set_player(item, xlistitem, mediaurl, view, strm):
    logger.info("platformtools set_player")
    # Si es un fichero strm no hace falta el play
    if strm:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xlistitem)
        if item.subtitle != "":
            xbmc.sleep(2000)
            xbmc.Player().setSubtitles(item.subtitle)

    # Movido del conector "torrent" aqui
    elif item.server == "torrent":
        play_torrent(item, xlistitem, mediaurl)
        return

    else:
        logger.info("player_mode="+config.get_setting("player_mode"))
        logger.info("mediaurl="+mediaurl)
        if config.get_setting("player_mode") == "3" or "megacrypter.com" in mediaurl:
            import download_and_play
            download_and_play.download_and_play(mediaurl, "download_and_play.tmp", config.get_setting("downloadpath"))
            return

        elif config.get_setting("player_mode") == "0" or \
                (config.get_setting("player_mode") == "3" and mediaurl.startswith("rtmp")):
            # Añadimos el listitem a una lista de reproducción (playlist)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            playlist.add(mediaurl, xlistitem)

            # Reproduce
            playersettings = config.get_setting('player_type')
            logger.info("pelisalacarta.platformcode.platformstools playersettings="+playersettings)

            if config.get_system_platform() == "xbox":
                player_type = xbmc.PLAYER_CORE_AUTO
                if playersettings == "0":
                    player_type = xbmc.PLAYER_CORE_AUTO
                    logger.info("pelisalacarta.platformcode.platformstools PLAYER_CORE_AUTO")
                elif playersettings == "1":
                    player_type = xbmc.PLAYER_CORE_MPLAYER
                    logger.info("pelisalacarta.platformcode.platformstools PLAYER_CORE_MPLAYER")
                elif playersettings == "2":
                    player_type = xbmc.PLAYER_CORE_DVDPLAYER
                    logger.info("pelisalacarta.platformcode.platformstools PLAYER_CORE_DVDPLAYER")

                xbmc_player = xbmc.Player(player_type)
            else:
                xbmc_player = xbmc.Player()

            xbmc_player.play(playlist, xlistitem)

        elif config.get_setting("player_mode") == "1":
            logger.info("mediaurl :" + mediaurl)
            logger.info("Tras setResolvedUrl")
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=mediaurl))

        elif config.get_setting("player_mode") == "2":
            xbmc.executebuiltin("PlayMedia("+mediaurl+")")

    # TODO MIRAR DE QUITAR VIEW
    if item.subtitle != "" and view:
        logger.info("Subtítulos externos: "+item.subtitle)
        xbmc.Player().setSubtitles(item.subtitle)


def play_torrent(item, xlistitem, mediaurl):
    logger.info("platformtools play_torrent")
    # Opciones disponibles para Reproducir torrents
    torrent_options = list()
    torrent_options.append(["Cliente interno (necesario libtorrent)"])
    torrent_options.append(["Cliente interno MCT (necesario libtorrent)"])

    # Plugins externos se pueden añadir otros
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.xbmctorrent")'):
        torrent_options.append(["Plugin externo: xbmctorrent", "plugin://plugin.video.xbmctorrent/play/%s"])
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.pulsar")'):
        torrent_options.append(["Plugin externo: pulsar", "plugin://plugin.video.pulsar/play?uri=%s"])
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.quasar")'):
        torrent_options.append(["Plugin externo: quasar", "plugin://plugin.video.quasar/play?uri=%s"])
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.stream")'):
        torrent_options.append(["Plugin externo: stream", "plugin://plugin.video.stream/play/%s"])
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.torrenter")'):
        torrent_options.append(["Plugin externo: torrenter",
                                "plugin://plugin.video.torrenter/?action=playSTRM&url=%s"])
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.torrentin")'):
        torrent_options.append(["Plugin externo: torrentin", "plugin://plugin.video.torrentin/?uri=%s&image="])

    if len(torrent_options) > 1:
        seleccion = dialog_select("Abrir torrent con...", [opcion[0] for opcion in torrent_options])
    else:
        seleccion = 0

    # Plugins externos
    if seleccion > 1:
        mediaurl = urllib.quote_plus(item.url)
        xbmc.executebuiltin("PlayMedia(" + torrent_options[seleccion][1] % mediaurl + ")")

    if seleccion == 1:
        from platformcode import mct
        mct.play(mediaurl, xlistitem, subtitle=item.subtitle)

    # Reproductor propio (libtorrent)
    if seleccion == 0:
        import time
        played = False

        # Importamos el cliente
        from btserver import Client

        # Iniciamos el cliente:
        c = Client(url=mediaurl, is_playing_fnc=xbmc.Player().isPlaying, wait_time=None, timeout=5,
                   temp_path=os.path.join(config.get_data_path(), "torrent"))

        # Mostramos el progreso
        progreso = dialog_progress("Pelisalacarta - Torrent", "Iniciando...")

        # Mientras el progreso no sea cancelado ni el cliente cerrado
        while not progreso.iscanceled() and not c.closed:
            try:
                # Obtenemos el estado del torrent
                s = c.status

                # Montamos las tres lineas con la info del torrent
                txt = '%.2f%% de %.1fMB %s | %.1f kB/s' % \
                      (s.progress_file, s.file_size, s.str_state, s._download_rate)
                txt2 = 'S: %d(%d) P: %d(%d) | DHT:%s (%d) | Trakers: %d' % \
                       (s.num_seeds, s.num_complete, s.num_peers, s.num_incomplete, s.dht_state, s.dht_nodes,
                        s.trackers)
                txt3 = 'Origen Peers TRK: %d DHT: %d PEX: %d LSD %d ' % \
                       (s.trk_peers, s.dht_peers, s.pex_peers, s.lsd_peers)

                progreso.update(s.buffer, txt, txt2, txt3)
                time.sleep(1)

                # Si el buffer se ha llenado y la reproduccion no ha sido iniciada, se inicia
                if s.buffer == 100 and not played:
                    # Cerramos el progreso
                    progreso.close()

                    # Obtenemos el playlist del torrent
                    videourl = c.get_play_list()

                    # Iniciamos el reproductor
                    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                    playlist.clear()
                    playlist.add(videourl, xlistitem)
                    xbmc_player = xbmc.Player()
                    xbmc_player.play(playlist)

                    # Marcamos como reproducido para que no se vuelva a iniciar
                    played = True

                    # Y esperamos a que el reproductor se cierre
                    while xbmc.Player().isPlaying():
                        time.sleep(1)

                    # Cuando este cerrado,  Volvemos a mostrar el dialogo
                    progreso = dialog_progress("Pelisalacarta - Torrent", "Iniciando...")

            except:
                import traceback
                logger.info(traceback.format_exc())
                break

        progreso.update(100, "Terminando y eliminando datos", " ", " ")

        # Detenemos el cliente
        if not c.closed:
            c.stop()

        # Y cerramos el progreso
        progreso.close()
