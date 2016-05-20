# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para biblioteca de pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import os
import re
import sys

import xbmc
from core import config
from core import logger
from core import scrapertools
from core.item import Item
from platformcode import library

# TODO repensar
librerias = os.path.join(config.get_runtime_path(), 'lib', 'samba')
if librerias not in sys.path:
    sys.path.append(librerias)

libreria_libsmb = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib', 'samba', 'libsmb'))
if libreria_libsmb not in sys.path:
    sys.path.append(libreria_libsmb)

import libsmb as samba

__channel__ = "biblioteca"
DEBUG = True


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.biblioteca mainlist")

    itemlist = list()
    itemlist.append(Item(channel=__channel__, action="peliculas", title="Películas"))
    itemlist.append(Item(channel=__channel__, action="series", title="Series"))
    # itemlist.append(Item(channel=__channel__, action="fichero_series", title="Fichero de series"))

    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    path = library.MOVIES_PATH
    itemlist = []
    aux_list = []

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
        #if not samba.usingsamba(i):
        strm_item = Item().fromurl(library.read_file(i))
        '''new_item = strm_item.clone(action=strm_item.action, path=i, from_biblioteca=True,
                                   title=os.path.splitext(os.path.basename(i))[0].capitalize(),
                                   extra=strm_item.extra)'''
        new_item = strm_item.clone(action="findvideos", path=i, from_biblioteca=True,
                                   title=os.path.splitext(os.path.basename(i))[0].capitalize(),
                                   extra=strm_item.extra)
        '''else:
            new_item = item.clone(action="play_strm", path=i,
                                  title=os.path.splitext(os.path.basename(i))[0].capitalize())'''

        # logger.debug(new_item.tostring('\n'))
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
        new_item = Item(channel=item.channel, action='get_temporadas', title=i, path=path)
        itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo='TVShows')

    return sorted(itemlist, key=lambda it: library.elimina_tildes(it.title).lower())


def get_temporadas(item):
    logger.info("pelisalacarta.channels.biblioteca get_temporadas")
    itemlist = []
    dict_temp = {}

    # Obtenemos las carpetas de los canales y los archivos de los capitulos
    if not samba.usingsamba(item.path):
        raiz, carpetas_series, ficheros = os.walk(item.path).next()
    else:
        raiz = item.path
        carpetas_series = samba.get_directories(item.path)
        ficheros = samba.get_files(item.path)

    if len(carpetas_series) > 1:
        # Si hay varios canales...
        for c in carpetas_series:
            # ...creamos un item por cada canal
            path = library.join_path(raiz, c)
            logger.debug(item.tostring('\n'))
            title = c
            canal = re.search('\[(.*?)\]', c)
            if canal:
                canal = canal.group(1).capitalize()
                title = "{0} [{1}]".format(item.title, canal)
            new_item = item.clone(action='get_temporadas', title=title, path=path)
            itemlist.append(new_item)

    elif len(carpetas_series) == 1:
        # ...si solo hay un canal...
        # ...obtenemos las temporadas de manera recursiva
        item.path = library.join_path(raiz, carpetas_series[0])
        return get_temporadas(item)
    else:
        # ...si ya estamos dentro del canal...
        # ...obtenemos las temporadas del listado de strm
        for i in ficheros:
            if i.endswith('.strm'):
                season = i.split('x')[0]
                dict_temp[season] = "Temporada " + str(season)

        # Creamos un item por cada temporada
        for season, title in dict_temp.items():
            new_item = item.clone(action='get_capitulos', title=title, contentSeason=season, contentEpisodeNumber="",
                                  filtrar_season=True)
            itemlist.append(new_item)
            logger.debug(new_item.tostring())

        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))
            new_item = item.clone(action='get_capitulos', title="*Todas las temporadas")
            itemlist.insert(0, new_item)

    return itemlist


def get_capitulos(item):
    logger.info("pelisalacarta.channels.biblioteca get_capitulos")
    itemlist = []
    logger.debug(item.tostring('\n'))
    # Obtenemos los archivos de los capitulos
    if not samba.usingsamba(item.path):
        raiz, carpetas_series, ficheros = os.walk(item.path).next()
    else:
        raiz = item.path
        ficheros = samba.get_files(item.path)

    # Crear un item en la lista para cada strm encontrado
    for i in ficheros:
        if i.endswith(".strm"):
            season, episode = scrapertools.get_season_and_episode(i).split("x")
            # Si hay q filtrar por temporada, ignoramos los capitulos de otras temporadas
            if item.filtrar_season and int(season) != int(item.contentSeason):
                continue

            path = library.join_path(raiz, i)
            #if not samba.usingsamba(raiz): TODO Esto no es necesario
            strm_item = Item().fromurl(library.read_file(path))
            new_item = item.clone(channel=strm_item.channel, action="findvideos", title=i, path=path,
                                  extra=strm_item.extra, url=strm_item.url, viewmode=strm_item.viewmode,
                                  contentEpisodeNumber=episode)
            '''else:
                new_item = item.clone(channel=item.channel, action="play_strm", title=i, path=path,
                                      contentEpisodeNumber=episode)'''

            itemlist.append(new_item)

    library.set_infoLabels_from_library(itemlist, tipo="Episodes")
    # return sorted(itemlist, key=get_sort_temp_epi)
    return sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))


def play_strm(item):
    logger.info("pelisalacarta.channels.biblioteca play_strm")
    itemlist = []

    strm_item = Item().fromurl(library.read_file(item.path))
    new_item = Item(channel=strm_item.channel, action=strm_item.action, title=strm_item.title, path=item.path,
                    extra=strm_item.extra, url=strm_item.url, viewmode=strm_item.viewmode)
    itemlist.append(new_item)

    return itemlist

'''
def get_sort_temp_epi(item):  # TODO SEitan: No se si esto es realmente necesario
    # logger.debug(item.tostring())
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
'''