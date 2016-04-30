# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para biblioteca de pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import os

from core import config
from core import jsontools
from core import logger
from core.item import Item

try:
    from platformcode import library
except ImportError:
    library = None

__channel__ = "biblioteca"
DEBUG = True


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.biblioteca mainlist")

    itemlist = list()
    if library:
        itemlist.append(Item(channel=__channel__, action="peliculas", title="Películas"))
        itemlist.append(Item(channel=__channel__, action="series", title="Series"))
        itemlist.append(Item(channel=__channel__, action="fichero_series", title="Fichero de series"))
    else:
        itemlist.append(Item(channel=__channel__, action="", title="Módulo de biblioteca no disponible para [{0}]".
                             format(config.get_platform())))
    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    path = library.MOVIES_PATH
    itemlist = []
    aux_list = list()

    # Obtenemos todos los strm de la biblioteca de CINE recursivamente
    for raiz, subcarpetas, ficheros in os.walk(path):
        aux_list.extend([os.path.join(raiz, f) for f in ficheros if os.path.splitext(f)[1] == ".strm"])

    # Crear un item en la lista para cada strm encontrado
    for i in aux_list:
        strm_item = Item().fromurl(library.read_file(i))
        new_item = strm_item.clone(action="findvideos", path=i,
                                   title=os.path.splitext(os.path.basename(i))[0].capitalize(), extra=strm_item.extra)
        itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo='Movies')
    return sorted(itemlist, key=lambda it: library.elimina_tildes(it.title).lower())


def series(item):
    logger.info("pelisalacarta.channels.biblioteca series")
    path = library.TVSHOWS_PATH
    itemlist = []

    # Obtenemos las carpetas de las series
    raiz, carpetas_series, files = os.walk(path).next()

    # Crear un item en la lista para cada carpeta encontrada
    for i in carpetas_series:
        new_item = Item(channel=item.channel, action='get_capitulos', title=i, path=os.path.join(raiz, i))
        itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo='TVShows')

    return sorted(itemlist, key=lambda it: library.elimina_tildes(it.title).lower())


def get_capitulos(item):
    logger.info("pelisalacarta.channels.biblioteca get_capitulos")
    itemlist = list()

    # Obtenemos los archivos de los capitulos
    raiz, carpetas_series, ficheros = os.walk(item.path).next()

    # Crear un item en la lista para cada strm encontrado
    for i in ficheros:
        if i.endswith('.strm'):

            path = os.path.join(raiz, i)
            strm_item = Item().fromurl(library.read_file(path))
            new_item = item.clone(channel=strm_item.channel, action="findvideos", title=i, path=path,
                                  extra=strm_item.extra, url=strm_item.url, viewmode=strm_item.viewmode)
            itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo='Episodes')
    return sorted(itemlist, key=lambda it:  it.title.lower())


def fichero_series(item):
    logger.info("pelisalacarta.channels.biblioteca fichero_series")

    itemlist = []

    tvshow_file = os.path.join(config.get_data_path(), library.TVSHOW_FILE)
    logger.info("leer el archivo: {0}".format(tvshow_file))

    dict_data = jsontools.load_json(library.read_file(tvshow_file))

    itemlist.append(Item(channel=item.channel, action="limpiar_fichero",
                         title="[COLOR yellow]Eliminar entradas de series huerfanas[/COLOR]", dict_fichero=dict_data))

    for channel in dict_data.keys():
        for tvshow in dict_data.get(channel).keys():
            itemlist.append(Item(channel=item.channel, action=item.action,
                                 title="[{channel}] {show}".format(channel=channel, show=tvshow)))

    return itemlist


def limpiar_fichero(item):
    logger.info("pelisalacarta.channels.biblioteca limpiar_fichero")

    # eliminar huerfanos
    return library.clean_up_file(item)
