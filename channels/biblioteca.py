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
from core import scrapertools
from core.item import Item
from lib.samba import libsmb as samba
from platformcode import library

__channel__ = "biblioteca"
DEBUG = True


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.biblioteca mainlist")

    itemlist = list()
    itemlist.append(Item(channel=__channel__, action="peliculas", title="Películas"))
    itemlist.append(Item(channel=__channel__, action="series", title="Series"))
    itemlist.append(Item(channel=__channel__, action="fichero_series", title="Fichero de series"))

    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    path = library.MOVIES_PATH
    itemlist = []
    aux_list = list()

    # Obtenemos todos los strm de la biblioteca de CINE recursivamente
    if not samba.usingsamba(path):
        for raiz, subcarpetas, ficheros in os.walk(path):
            aux_list.extend([os.path.join(raiz, f) for f in ficheros if os.path.splitext(f)[1] == ".strm"])
    else:
        raiz = path
        ficheros, subcarpetas = samba.get_files_and_directories(raiz)
        aux_list.extend([library.join_path(raiz, f) for f in ficheros if os.path.splitext(f)[1] == ".strm"])
        for carpeta in subcarpetas:
            carpeta = library.join_path(raiz, carpeta)
            for _file in samba.get_files(carpeta):
                if os.path.splitext(_file)[1] == ".strm":
                    aux_list.extend([library.join_path(carpeta, _file)])

    # Crear un item en la lista para cada strm encontrado
    for i in aux_list:
        if not samba.usingsamba(i):
            strm_item = Item().fromurl(library.read_file(i))
            new_item = strm_item.clone(action=strm_item.action, path=i,
                                       title=os.path.splitext(os.path.basename(i))[0].capitalize(),
                                       extra=strm_item.extra)
        else:
            new_item = item.clone(action="play_strm", path=i,
                                  title=os.path.splitext(os.path.basename(i))[0].capitalize())

        itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo='Movies')
    return sorted(itemlist, key=lambda it: library.elimina_tildes(it.title).lower())


def series(item):
    logger.info("pelisalacarta.channels.biblioteca series")
    path = library.TVSHOWS_PATH
    itemlist = []

    # Obtenemos las carpetas de las series
    if not samba.usingsamba(path):
        raiz, carpetas_series, files = os.walk(path).next()
    else:
        raiz = path
        carpetas_series = samba.get_directories(path)

    # Crear un item en la lista para cada carpeta encontrada
    for i in carpetas_series:
        path = library.join_path(raiz, i)
        new_item = Item(channel=item.channel, action='get_capitulos', title=i, path=path)
        itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo='TVShows')

    return sorted(itemlist, key=lambda it: library.elimina_tildes(it.title).lower())


def get_capitulos(item):
    logger.info("pelisalacarta.channels.biblioteca get_capitulos")
    itemlist = list()

    # Obtenemos los archivos de los capitulos
    if not samba.usingsamba(item.path):
        raiz, carpetas_series, ficheros = os.walk(item.path).next()
    else:
        raiz = item.path
        ficheros = samba.get_files(item.path)

    # Crear un item en la lista para cada strm encontrado
    for i in ficheros:
        if i.endswith('.strm'):

            path = library.join_path(raiz, i)
            if not samba.usingsamba(raiz):
                strm_item = Item().fromurl(library.read_file(path))
                new_item = item.clone(channel=strm_item.channel, action="findvideos", title=i, path=path,
                                      extra=strm_item.extra, url=strm_item.url, viewmode=strm_item.viewmode)
            else:
                new_item = item.clone(channel=item.channel, action="play_strm", title=i, path=path)

            itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo='Episodes')
    return sorted(itemlist, key=get_sort_temp_epi)


def play_strm(item):
    logger.info("pelisalacarta.channels.biblioteca play_strm")
    itemlist = list()

    strm_item = Item().fromurl(library.read_file(item.path))
    new_item = Item(channel=strm_item.channel, action=strm_item.action, title=strm_item.title, path=item.path,
                    extra=strm_item.extra, url=strm_item.url, viewmode=strm_item.viewmode)
    itemlist.append(new_item)

    return itemlist


def get_sort_temp_epi(item):
    if item.infoLabels:
        return int(item.infoLabels.get('season', "1")), int(item.infoLabels.get('episode', "1"))
    else:
        temporada, capitulo = scrapertools.get_season_and_episode(item.title.lower()).split('x')
        return int(temporada), int(capitulo)


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
