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
# --------------------------------------------------------------------------------
# renumeratetools - se encarga de renumerar episodios
# --------------------------------------------------------------------------------

import os

import xbmcgui
from core import config
from core import filetools
from core import jsontools
from core import logger
from core.item import Item
from platformcode import platformtools


TAG_TVSHOW_RENUMERATE = "TVSHOW_RENUMBER"
TAG_SEASON_EPISODE = "season_episode"
__channel__ = "renumeratetools"


def context():
    _context = ""
    '''
    configuración para mostrar la opción de renumeración, actualmente sólo se permite en xbmc, se cambiará cuando
    'platformtools.show_channel_settings' esté disponible para las distintas plataformas
    '''
    if config.is_xbmc():
        _context = [{"title": "RENUMERAR",
                     "action": "config_item",
                     "channel": "renumeratetools"}]

    return _context

context = context()


def show_option(channel, itemlist):
    itemlist.append(Item(channel=__channel__, title="[COLOR yellow]Configurar renumeración en series...[/COLOR]",
                         action="load", from_channel=channel))

    return itemlist


def load(item):
    return mainlist(channel=item.from_channel)


def get_tvshows(from_channel):
    """
    Obtiene las series renumeradas de un canal

    :param from_channel: canal que tiene las series renumeradas
    :type from_channel: str
    :return: dict con las series
    :rtype: dict
    """
    logger.info()
    dict_series = {}
    name_file = from_channel

    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))

    fname = os.path.join(config.get_data_path(), "settings_channels", name_file + "_data.json")

    data = filetools.read(fname)
    dict_data = jsontools.load_json(data)

    check_json_file(data, fname, dict_data)

    if TAG_TVSHOW_RENUMERATE in dict_data:
        dict_series = dict_data[TAG_TVSHOW_RENUMERATE]

    logger.debug("json_series: {0}".format(dict_series))

    return dict_series


def mainlist(channel):
    """
    Muestra una lista de las series renumeradas

    :param channel: nombre del canal para obtener las series renumeradas
    :type channel: str
    :return: lista de Item
    :rtype: list[Item]
    """
    logger.info()
    itemlist = []
    dict_series = get_tvshows(channel)

    idx = 0
    for tvshow in sorted(dict_series):
        tag_color = "0xff008000"
        if idx % 2 == 0:
            tag_color = "blue"

        idx += 1
        name = tvshow
        title = "Configurar [COLOR {0}][{1}][/COLOR]".format(tag_color, name)

        itemlist.append(Item(channel=__channel__, action="config_item", title=title, show=name, from_channel=channel))

    if len(itemlist) == 0:
        itemlist.append(Item(channel=channel, action="mainlist",
                             title="No se han encontrado series, busca una serie y pulsa en menú contextual "
                                   "'RENUMERAR'"))

    return itemlist


def config_item(item):
    """
    muestra una serie renumerada para su configuración

    :param item: item
    :type item: Item
    """
    logger.info("item {0}".format(item.tostring("\n")))

    dict_series = get_tvshows(item.from_channel)
    data = dict_series.get(item.show, {})

    # if data:
    #     opciones = ["Editar", "Borrar", "Añadir temporada"]
    #     selected = platformtools.dialog_select("¿Qué desea hacer?", opciones)
    #
    #     if selected == 0:
    #         return show_season(item)
    #     elif selected == 1:
    #         borrar(item)
    #     elif selected == 2:
    #         return add_season(item)
    # else:
    #     return add_season(item)

    list_controls = {}
    custom_button = {}

    RenumerateWindow("RenumerateWindow.xml", config.get_runtime_path())
    # tbd = RenumerateWindow("DialogTextViewer.xml", os.getcwd(), "Default")
    # tbd.ask("titulo", "argumento", "")

    # platformtools.show_channel_settings(list_controls=list_controls, callback='guardar_valores', item=item,
    #                                     caption="Filtrado de enlaces para: [COLOR blue]{0}[/COLOR]".format(item.show),
    #                                     custom_button=custom_button)



# def show_season(item):
#     logger.info()
#     logger.info("item " + item.tostring("\n"))
#     itemlist = []
#
#     dict_series = get_tvshows(item.from_channel)
#     data = dict_series.get(item.show, {}).get(TAG_SEASON_EPISODE, [])
#
#     for e in data:
#         title = "Configurar [Temporada: %s empieza desde episodio: %s]" % (e[0], e[1])
#         itemlist.append(Item(channel=__channel__, action="add_season", title=title))
#
#     return itemlist


def borrar(item):

    heading = "¿Está seguro que desea eliminar renumeración?"
    line1 = "Pulse 'Si' para eliminar la renumeración de [COLOR blue]{0}[/COLOR], pulse 'No' o cierre la ventana " \
            "para no hacer nada.".format(item.show.strip())

    if platformtools.dialog_yesno(heading, line1) == 1:
        dict_series = get_tvshows(item.from_channel)
        dict_series.pop(item.show, None)

        fname, json_data = update_json_data(dict_series, item.from_channel)
        result = filetools.write(fname, json_data)

        if result:
            message = "FILTRO ELIMINADO"
        else:
            message = "Error al guardar en disco"

        heading = item.show.strip()
        platformtools.dialog_notification(heading, message)
        # logger.info("he pulsado sobre eliminar")


def add_season(item):
    logger.info("item {0}".format(item.tostring("\n")))

    # OBTENEMOS LOS DATOS DEL JSON
    dict_series = get_tvshows(item.from_channel)
    tvshow = item.show.strip()
    list_season_episode = dict_series.get(tvshow, {}).get(TAG_SEASON_EPISODE, [])

    heading = "Introduzca el número de la temporada"
    default = 2
    if list_season_episode:
        # mostrar temporada + 1 de la lista
        default = list_season_episode[0][0]+1

    season = platformtools.dialog_numeric(0, heading, str(default))

    # si hemos insertado un valor en la temporada
    if season != "" and int(season) > 0:
        heading = "Introduzca el número de episodio desde que empieza la temporada"
        default = 0
        if list_season_episode:
            for e in list_season_episode:
                # mostrar suma episodios de la lista
                default += e[1]
        episode = platformtools.dialog_numeric(0, heading, str(default))

        # si hemos insertado un valor en el episodio
        if episode != "":
            if list_season_episode:
                list_season_episode.insert(0, [int(season), int(episode)])
                new_list_season_episode = list_season_episode[:]
                dict_renumerate = {TAG_SEASON_EPISODE: new_list_season_episode}
            else:
                dict_renumerate = {TAG_SEASON_EPISODE: [[int(season), int(episode)]]}

            dict_series[tvshow] = dict_renumerate

            fname, json_data = update_json_data(dict_series, item.from_channel)
            result = filetools.write(fname, json_data)

            if result:
                message = "FILTRO GUARDADO"
            else:
                message = "Error al guardar en disco"

            heading = item.show.strip()
            platformtools.dialog_notification(heading, message)


def check_json_file(data, fname, dict_data):
    """
    Comprueba que si dict_data(conversion del fichero JSON a dict) no es un diccionario, se genere un fichero con
    data de nombre fname.bk.

    :param data: contenido del fichero fname
    :type data: str
    :param fname: nombre del fichero leido
    :type fname: str
    :param dict_data: nombre del diccionario
    :type dict_data: dict
    """
    logger.info()
    if not dict_data:
        logger.error("Error al cargar el json del fichero {0}".format(fname))

        if data != "":
            # se crea un nuevo fichero
            title = filetools.write("{0}.bk".format(fname), data)
            if title != "":
                logger.error("Ha habido un error al guardar el fichero: {0}.bk"
                             .format(fname))
            else:
                logger.debug("Se ha guardado una copia con el nombre: {0}.bk"
                             .format(fname))
        else:
            logger.debug("Está vacío el fichero: {0}".format(fname))


def update_json_data(dict_series, filename):
    """
    actualiza el json_data de un fichero con el diccionario pasado

    :param dict_series: diccionario con las series
    :type dict_series: dict
    :param filename: nombre del fichero para guardar
    :type filename: str
    :return: fname, json_data
    :rtype: str, dict
    """
    logger.info()
    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))
    fname = os.path.join(config.get_data_path(), "settings_channels", filename + "_data.json")
    data = filetools.read(fname)
    dict_data = jsontools.load_json(data)
    # es un dict
    if dict_data:
        if TAG_TVSHOW_RENUMERATE in dict_data:
            logger.info("   existe el key SERIES")
            dict_data[TAG_TVSHOW_RENUMERATE] = dict_series
        else:
            logger.info("   NO existe el key SERIES")
            new_dict = {TAG_TVSHOW_RENUMERATE: dict_series}
            dict_data.update(new_dict)
    else:
        logger.info("   NO es un dict")
        dict_data = {TAG_TVSHOW_RENUMERATE: dict_series}
    json_data = jsontools.dump_json(dict_data)
    return fname, json_data


# Create a skinned textbox window
class TextBox(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        pass

    def onInit(self):
        try:
            self.getControl(5).setText(self.text)
            self.getControl(1).setLabel(self.title)
        except:
            pass

    def onClick(self, controlId):
        pass

    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        self.close()

    def ask(self, title, text, image):
        self.title = title
        self.text = text
        self.doModal()


class RenumerateWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        logger.debug("mojonazo")
        # Changing the three varibles passed won't change, anything
        # Doing strXMLname = "bah.xml" will not change anything.
        # don't put GUI sensitive stuff here (as the xml hasn't been read yet
        # Idea to initialize your variables here
        pass

    def onInit(self):
        # try:
        #     self.getControl(5).setText(self.text)
        #     self.getControl(1).setLabel(self.title)
        # except:
        #     pass
        pass

    def onClick(self, controlId):
        pass

    def onFocus(self, controlId):
        pass

    def onAction(self, action):
        pass
        # self.close()

    # def ask(self, title, text, image):
    #     self.title = title
    #     self.text = text
    #     self.doModal()
