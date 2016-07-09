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
# Library Tools
# ------------------------------------------------------------

import errno
import math
import os
import re
import sys
import urllib
import urllib2

import xbmc

from core import config
from core import filetools
from core import jsontools
from core import logger
from core import scrapertools
from core.item import Item
from platformcode import platformtools

modo_cliente = int(config.get_setting("library_mode"))
# Host name where XBMC is running, leave as localhost if on this PC
# Make sure "Allow control of XBMC via HTTP" is set to ON in Settings ->
# Services -> Webserver
xbmc_host = config.get_setting("xbmc_host")
# Configured in Settings -> Services -> Webserver -> Port
xbmc_port = int(config.get_setting("xbmc_port"))
# Base URL of the json RPC calls. For GET calls we append a "request" URI
# parameter. For POSTs, we add the payload as JSON the the HTTP request body
xbmc_json_rpc_url = "http://{host}:{port}/jsonrpc".format(host=xbmc_host, port=xbmc_port)

DEBUG = config.get_setting("debug")

LIBRARY_PATH = config.get_library_path()
if not filetools.exists(LIBRARY_PATH):
    logger.info("pelisalacarta.platformcode.library Library path doesn't exist:" + LIBRARY_PATH)
    config.verify_directories_created()

# TODO permitir cambiar las rutas y nombres en settings para 'cine' y 'series'
FOLDER_MOVIES = "CINE"  # config.get_localized_string(30072)
MOVIES_PATH = filetools.join(LIBRARY_PATH, FOLDER_MOVIES)
if not filetools.exists(MOVIES_PATH):
    logger.info("pelisalacarta.platformcode.library Movies path doesn't exist:" + MOVIES_PATH)
    filetools.exists(MOVIES_PATH)

FOLDER_TVSHOWS = "SERIES"  # config.get_localized_string(30073)
TVSHOWS_PATH = filetools.join(LIBRARY_PATH, FOLDER_TVSHOWS)
if not filetools.exists(TVSHOWS_PATH):
    logger.info("pelisalacarta.platformcode.library Tvshows path doesn't exist:" + TVSHOWS_PATH)
    filetools.mkdir(TVSHOWS_PATH)

TVSHOW_FILE = "series.json"
TVSHOW_FILE_OLD = "series.xml"

# Versions compatible with JSONRPC v6
LIST_PLATFORM_COMPATIBLE = ["xbmc-frodo", "xbmc-gotham", "kodi-helix", "kodi-isengard", "kodi-jarvis"]


def is_compatible():
    """
    comprueba si la plataforma es xbmc/Kodi, la version es compatible y si está configurada la libreria en Kodi.
    @rtype:   bool
    @return:  si es compatible.

    """
    logger.info("pelisalacarta.platformcode.library is_compatible")
    if config.get_platform() in LIST_PLATFORM_COMPATIBLE and library_in_kodi():
        return True
    else:
        return False


def library_in_kodi():
    """
    comprueba si la libreria de pelisalacarta está configurada en xbmc/Kodi
    @rtype:   bool
    @return:  si está configurada la libreria en xbmc/Kodi.
    """
    logger.info("pelisalacarta.platformcode.library library_in_kodi")
    # TODO arreglar
    return True

    path = xbmc.translatePath(os.path.join("special://profile/", "sources.xml"))
    data = read_file(path)

    if config.get_library_path() in data:
        return True
    else:
        return False


def save_library_movie(item):
    """
    guarda en la libreria de peliculas el elemento item, con los valores que contiene.
    @type item: item
    @param item: elemento que se va a guardar.
    @rtype insertados: int
    @return:  el número de elementos insertados
    @rtype sobreescritos: int
    @return:  el número de elementos sobreescritos
    @rtype fallidos: int
    @return:  el número de elementos fallidos o -1 si ha fallado todo
    """
    logger.info("pelisalacarta.platformcode.library savelibrary_movie")
    insertados = 0
    sobreescritos = 0
    fallidos = 0
    logger.debug(item.tostring('\n'))

    if not item.fulltitle or not item.channel:
        return 0, 0, -1  # Salimos sin guardar

    # progress dialog
    p_dialog = platformtools.dialog_progress('pelisalacarta', 'Añadiendo película...')
    filename = filetools.title_to_filename("{0} [{1}].strm".format(item.fulltitle.strip().lower(),
                                                                   item.channel))
    logger.debug(filename)
    fullfilename = filetools.join(MOVIES_PATH, filename)
    addon_name = sys.argv[0].strip()
    if not addon_name:
        addon_name = "plugin://plugin.video.pelisalacarta/"

    if filetools.exists(fullfilename):
        logger.info("pelisalacarta.platformcode.library savelibrary el fichero existe. Se sobreescribe")
        sobreescritos += 1
    else:
        insertados += 1

    p_dialog.update(100, 'Añadiendo película...', item.fulltitle)
    p_dialog.close()

    if filetools.write(fullfilename, '{addon}?{url}'.format(addon=addon_name, url=item.tourl())):
        item = get_video_id_from_scraper(item, config.get_setting("scrap_ask_name") == "true", "movie")
        if 'id_Tmdb' in item.infoLabels:
            create_nfo_file(item.infoLabels['id_Tmdb'], fullfilename[:-5], "cine")
        return insertados, sobreescritos, fallidos
    else:
        return 0, 0, 1


def save_library_tvshow(serie, episodelist):
    """
    guarda en la libreria de series la serie con todos los capitulos incluidos en la lista episodelist
    @type serie: item
    @param serie: item que representa la serie a guardar
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos o -1 si ha fallado toda la serie
    """
    logger.info("pelisalacarta.platformcode.library savelibrary_tvshow")

    if serie.show == "":  # TODO ¿otras opciones?
        return 0, 0, -1  # Salimos sin guardar: La serie no tiene el titulo fijado

    path = filetools.join(TVSHOWS_PATH, "{0} [{1}]".format(filetools.title_to_filename(serie.show.strip().lower()),
                                                           serie.channel).lower())
    if not filetools.exists(path):
        logger.info("pelisalacarta.platformcode.library savelibrary Creando directorio serie:" + path)
        try:
            filetools.mkdir(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    # Guardar los episodios
    insertados, sobreescritos, fallidos = save_library_episodes(path, episodelist)

    return insertados, sobreescritos, fallidos


# TODO esto se borra
def get_dict_series():
    """
    devuelve un diccionario con las series obtenidas de 'series.json'
    @rtype dict_series: dict
    @return:  diccionario con las series.
    """
    logger.info("pelisalacarta.platformcode.library get_dict_series")
    fname = filetools.join(config.get_data_path(), TVSHOW_FILE)
    dict_series = jsontools.load_json(filetools.read(fname))

    if dict_series == "":
        dict_series = {}

    return dict_series


def get_video_id_from_scraper(serie, ask=False, scraper="tmdb", video_type="tv"):
    """
    Hace una busqueda con el scraper seleccionado *tmdb por defecto* por el nombre (y año si esta presente) y presenta
    una 'ventana' para seleccionar uno.
    Retorna el item pasado como parametro con algunos infoLabels actualizados
    @type serie: item
    @param serie: video para obtener identificar
    @type ask: bool
    @param ask: muestra la ventana de información para seleccionar el titulo correcto de la serie/pelicula.
    @type scraper: str
    @param scraper: scraper para obtener la información de la serie // de momento sólo es tmdb
    @type video_type: str
    @param video_type: tipo de video para buscar, 'tv' o 'movie'
    @rtype serie: item
    @return:  devuelve el item 'serie' con la información seteada.
    """
    logger.info("pelisalacarta.platformcode.library get_video_id_from_scraper")
    from core import tmdb
    otmdb = tmdb.Tmdb(texto_buscado=serie.infoLabels['title'], tipo=video_type, year=serie.infoLabels.get('year', ''))
    if ask:
        select = platformtools.show_video_info(otmdb.get_list_resultados(),
                                               caption="[{0}]: Selecciona la serie correcta".
                                               format(serie.infoLabels['title']), callback='cb_select_from_tmdb')
        if select:
            serie.infoLabels.update(select)
            logger.debug(tmdb.infoLabels_tostring(serie))
    else:
        if len(otmdb.get_list_resultados()) == 0:
            return serie

        # Fijamos los infoLabels
        serie.infoLabels.update(otmdb.get_list_resultados()[0])
        serie.infoLabels['id_Tmdb'] = otmdb.get_list_resultados()[0]['id']
        serie.infoLabels['title'] = otmdb.get_list_resultados()[0]['name'].strip()  # Si fuesen movies seria title

    return serie


def cb_select_from_tmdb(dic):
    # print repr(dic)
    return dic


def save_library_episodes(path, episodelist):
    """
    guarda en la ruta indicada todos los capitulos incluidos en la lista episodelist
    @type path: str
    @param path: ruta donde guardar los episodios
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos
    """
    logger.info("pelisalacarta.platformcode.library savelibrary_episodes")
    insertados = 0
    sobreescritos = 0
    fallidos = 0

    # progress dialog
    p_dialog = platformtools.dialog_progress('pelisalacarta', 'Añadiendo episodios...')
    p_dialog.update(0, 'Añadiendo episodio...')
    # fix float porque la division se hace mal en python 2.x
    t = float(100) / len(episodelist)

    addon_name = sys.argv[0].strip()
    if not addon_name:
        addon_name = "plugin://plugin.video.pelisalacarta/"

    for i, e in enumerate(episodelist):
        p_dialog.update(int(math.ceil(i * t)), 'Añadiendo episodio...', e.title)
        # Añade todos menos el que dice "Añadir esta serie..." o "Descargar esta serie..."
        if e.action == "add_serie_to_library" or e.action == "download_all_episodes":
            continue

        e.action = "play_from_library"
        e.category = "Series"

        nuevo = False
        filename = "{0}.strm".format(scrapertools.get_season_and_episode(e.title.lower()))
        fullfilename = filetools.join(path, filename)
        # logger.debug(fullfilename)

        if not filetools.exists(fullfilename):
            nuevo = True

        if filetools.write(fullfilename, '{addon}?{url}'.format(addon=addon_name, url=e.tourl())):
            if nuevo:
                insertados += 1
            else:
                sobreescritos += 1
        else:
            fallidos += 1

        if p_dialog.iscanceled():
            break

    p_dialog.close()

    logger.debug("insertados= {0}, sobreescritos={1}, fallidos={2}".format(insertados, sobreescritos, fallidos))
    return insertados, sobreescritos, fallidos


def set_info_labels(itemlist, path):
    """
    guarda los datos (thumbnail, fanart, plot, actores, etc) a mostrar del fichero tvshow.json
    @type itemlist: list
    @param itemlist: item
    @type path: str
    @param path:
    @rtype:   infoLabels
    @return:  result of saving.
    """
    logger.info("pelisalacarta.platformcode.library set_info_labels")
    path = filetools.join(path, "tvshow.json")
    dict_data = jsontools.load_json(filetools.read(path))
    for i in itemlist:

        i.title = dict_data['title']


    # payload = dict()
    # result = list()
    #
    # if tipo == 'Movies':
    #     payload = {"jsonrpc": "2.0",
    #                "method": "VideoLibrary.GetMovies",
    #                "params": {"properties": ["title", "year", "rating", "trailer", "tagline", "plot", "plotoutline",
    #                                          "originaltitle", "lastplayed", "playcount", "writer", "mpaa", "cast",
    #                                          "imdbnumber", "runtime", "set", "top250", "votes", "fanart", "tag",
    #                                          "thumbnail", "file", "director", "country", "studio", "genre",
    #                                          "sorttitle", "setid", "dateadded"
    #                                          ]},
    #                "id": "libMovies"}
    #
    # elif tipo == 'TVShows':
    #     payload = {"jsonrpc": "2.0",
    #                "method": "VideoLibrary.GetTVShows",
    #                "params": {"properties": ["title", "genre", "year", "rating", "plot", "studio", "mpaa", "cast",
    #                                          "playcount", "episode", "imdbnumber", "premiered", "votes", "lastplayed",
    #                                          "fanart", "thumbnail", "file", "originaltitle", "sorttitle",
    #                                          "episodeguide", "season", "watchedepisodes", "dateadded", "tag"
    #                                          ]},
    #                "id": "libTvShows"}
    #
    # elif tipo == 'Episodes' and 'tvshowid' in itemlist[0].infoLabels and itemlist[0].infoLabels['tvshowid']:
    #     tvshowid = itemlist[0].infoLabels['tvshowid']
    #     payload = {"jsonrpc": "2.0",
    #                "method": "VideoLibrary.GetEpisodes",
    #                "params": {"tvshowid": tvshowid,
    #                           "properties": ["title", "plot", "votes", "rating", "writer", "firstaired", "playcount",
    #                                          "runtime", "director", "productioncode", "season", "episode",
    #                                          "originaltitle",
    #                                          "showtitle", "cast", "lastplayed", "fanart", "thumbnail",
    #                                          "file", "dateadded", "tvshowid"
    #                                          ]},
    #                "id": 1}
    #
    # data = get_data(payload)
    # logger.debug("JSON-RPC: {0}".format(data))
    #
    # if 'error' in data:
    #     logger.error("JSON-RPC: {0}".format(data))
    #
    # elif 'movies' in data['result']:
    #     result = data['result']['movies']
    #
    # elif 'tvshows' in data['result']:
    #     result = data['result']['tvshows']
    #
    # elif 'episodes' in data['result']:
    #     result = data['result']['episodes']
    #
    # if result:
    #     for i in itemlist:
    #         for r in result:
    #             r_filename_aux = r['file'][:-1] if r['file'].endswith(os.sep) or r['file'].endswith('/') else r['file']
    #             r_filename = os.path.basename(r_filename_aux)
    #             # logger.debug(os.path.basename(i.path) + '\n' + r_filename)
    #             i_filename = os.path.basename(i.path)
    #             if i_filename == r_filename:
    #                 infoLabels = r
    #
    #                 # Obtener imagenes y asignarlas al item
    #                 if 'thumbnail' in infoLabels:
    #                     infoLabels['thumbnail'] = urllib.unquote_plus(infoLabels['thumbnail']).replace('image://', '')
    #                     i.thumbnail = infoLabels['thumbnail'][:-1] if infoLabels['thumbnail'].endswith('/') else \
    #                         infoLabels['thumbnail']
    #                 if 'fanart' in infoLabels:
    #                     infoLabels['fanart'] = urllib.unquote_plus(infoLabels['fanart']).replace('image://', '')
    #                     i.fanart = infoLabels['fanart'][:-1] if infoLabels['fanart'].endswith('/') else infoLabels[
    #                         'fanart']
    #
    #                 # Adaptar algunos campos al formato infoLables
    #                 if 'cast' in infoLabels:
    #                     l_castandrole = list()
    #                     for c in sorted(infoLabels['cast'], key=lambda _c: _c["order"]):
    #                         l_castandrole.append((c['name'], c['role']))
    #                     infoLabels.pop('cast')
    #                     infoLabels['castandrole'] = l_castandrole
    #                 if 'genre' in infoLabels:
    #                     infoLabels['genre'] = ', '.join(infoLabels['genre'])
    #                 if 'writer' in infoLabels:
    #                     infoLabels['writer'] = ', '.join(infoLabels['writer'])
    #                 if 'director' in infoLabels:
    #                     infoLabels['director'] = ', '.join(infoLabels['director'])
    #                 if 'country' in infoLabels:
    #                     infoLabels['country'] = ', '.join(infoLabels['country'])
    #                 if 'studio' in infoLabels:
    #                     infoLabels['studio'] = ', '.join(infoLabels['studio'])
    #                 if 'runtime' in infoLabels:
    #                     infoLabels['duration'] = infoLabels.pop('runtime')
    #
    #                 # Fijar el titulo si existe y añadir infoLabels al item
    #                 if 'label' in infoLabels:
    #                     i.title = infoLabels['label']
    #                 i.infoLabels = infoLabels
    #                 result.remove(r)
    #                 break


def set_infoLabels_from_library(itemlist, tipo):
    """
    guarda los datos (thumbnail, fanart, plot, actores, etc) a mostrar de la library de Kodi.
    @type itemlist: list
    @param itemlist: item
    @type tipo: str
    @param tipo:
    @rtype:   infoLabels
    @return:  result of saving.
    """
    logger.info("pelisalacarta.platformcode.library set_infoLabels_from_library")
    payload = dict()
    result = list()

    if tipo == 'Movies':
        payload = {"jsonrpc": "2.0",
                   "method": "VideoLibrary.GetMovies",
                   "params": {"properties": ["title", "year", "rating", "trailer", "tagline", "plot", "plotoutline",
                                             "originaltitle", "lastplayed", "playcount", "writer", "mpaa", "cast",
                                             "imdbnumber", "runtime", "set", "top250", "votes", "fanart", "tag",
                                             "thumbnail", "file", "director", "country", "studio", "genre",
                                             "sorttitle", "setid", "dateadded"
                                             ]},
                   "id": "libMovies"}

    elif tipo == 'TVShows':
        payload = {"jsonrpc": "2.0",
                   "method": "VideoLibrary.GetTVShows",
                   "params": {"properties": ["title", "genre", "year", "rating", "plot", "studio", "mpaa", "cast",
                                             "playcount", "episode", "imdbnumber", "premiered", "votes", "lastplayed",
                                             "fanart", "thumbnail", "file", "originaltitle", "sorttitle",
                                             "episodeguide", "season", "watchedepisodes", "dateadded", "tag"
                                             ]},
                   "id": "libTvShows"}

    elif tipo == 'Episodes' and 'tvshowid' in itemlist[0].infoLabels and itemlist[0].infoLabels['tvshowid']:
        tvshowid = itemlist[0].infoLabels['tvshowid']
        payload = {"jsonrpc": "2.0",
                   "method": "VideoLibrary.GetEpisodes",
                   "params": {"tvshowid": tvshowid,
                              "properties": ["title", "plot", "votes", "rating", "writer", "firstaired", "playcount",
                                             "runtime", "director", "productioncode", "season", "episode",
                                             "originaltitle",
                                             "showtitle", "cast", "lastplayed", "fanart", "thumbnail",
                                             "file", "dateadded", "tvshowid"
                                             ]},
                   "id": 1}

    data = get_data(payload)
    logger.debug("JSON-RPC: {0}".format(data))

    if 'error' in data:
        logger.error("JSON-RPC: {0}".format(data))

    elif 'movies' in data['result']:
        result = data['result']['movies']

    elif 'tvshows' in data['result']:
        result = data['result']['tvshows']

    elif 'episodes' in data['result']:
        result = data['result']['episodes']

    if result:
        for i in itemlist:
            for r in result:
                r_filename_aux = r['file'][:-1] if r['file'].endswith(os.sep) or r['file'].endswith('/') else r['file']
                r_filename = os.path.basename(r_filename_aux)
                # logger.debug(os.path.basename(i.path) + '\n' + r_filename)
                i_filename = os.path.basename(i.path)
                if i_filename == r_filename:
                    infoLabels = r

                    # Obtener imagenes y asignarlas al item
                    if 'thumbnail' in infoLabels:
                        infoLabels['thumbnail'] = urllib.unquote_plus(infoLabels['thumbnail']).replace('image://', '')
                        i.thumbnail = infoLabels['thumbnail'][:-1] if infoLabels['thumbnail'].endswith('/') else \
                            infoLabels['thumbnail']
                    if 'fanart' in infoLabels:
                        infoLabels['fanart'] = urllib.unquote_plus(infoLabels['fanart']).replace('image://', '')
                        i.fanart = infoLabels['fanart'][:-1] if infoLabels['fanart'].endswith('/') else infoLabels[
                            'fanart']

                    # Adaptar algunos campos al formato infoLables
                    if 'cast' in infoLabels:
                        l_castandrole = list()
                        for c in sorted(infoLabels['cast'], key=lambda _c: _c["order"]):
                            l_castandrole.append((c['name'], c['role']))
                        infoLabels.pop('cast')
                        infoLabels['castandrole'] = l_castandrole
                    if 'genre' in infoLabels:
                        infoLabels['genre'] = ', '.join(infoLabels['genre'])
                    if 'writer' in infoLabels:
                        infoLabels['writer'] = ', '.join(infoLabels['writer'])
                    if 'director' in infoLabels:
                        infoLabels['director'] = ', '.join(infoLabels['director'])
                    if 'country' in infoLabels:
                        infoLabels['country'] = ', '.join(infoLabels['country'])
                    if 'studio' in infoLabels:
                        infoLabels['studio'] = ', '.join(infoLabels['studio'])
                    if 'runtime' in infoLabels:
                        infoLabels['duration'] = infoLabels.pop('runtime')

                    # Fijar el titulo si existe y añadir infoLabels al item
                    if 'label' in infoLabels:
                        i.title = infoLabels['label']
                    i.infoLabels = infoLabels
                    result.remove(r)
                    break


def save_tvshow_json(serie):
    """
    Guarda los datos de la serie dentro del fichero 'tvshow.json'
    @type serie: item
    @param serie: datos de la serie
    """
    logger.info("pelisalacarta.platformcode.library save_tvshow_json")
    fname = filetools.join(config.get_data_path(), TVSHOW_FILE)

    if not filetools.isfile(fname):
        upgrade_library()

    if 'infoLabels' not in serie:
        serie.infoLabels = {}

    patron = "^(.+)[\s]\((\d{4})\)$"
    matches = re.compile(patron, re.DOTALL).findall(serie.show)

    if matches:
        serie.infoLabels['title'] = matches[0][0]
        serie.infoLabels['year'] = matches[0][1]

    if 'title' not in serie.infoLabels:
        serie.infoLabels['title'] = serie.show

    # TODO de momento es el unico, cuando haya más se podrá configurar
    scraper = "tmdb"

    # Abrir ventana de seleccion de serie
    serie = get_video_id_from_scraper(serie, config.get_setting("scrap_ask_name") == "true", scraper=scraper)

    scrape_id = ""
    if scraper == "tmdb":
        scrape_id = "id_Tmdb"

    create_nfo = False
    if scrape_id in serie.infoLabels:
        tvshow_id = serie.infoLabels[scrape_id]
        create_nfo = True
    else:
        tvshow_id = "t_{0}_[{1}]".format(serie.show.strip().replace(" ", "_"), serie.channel)

    # Cargar el registro series.json
    path = filetools.join(TVSHOWS_PATH, "{0} [{1}]".format(filetools.title_to_filename(serie.show.strip().lower()),
                                                           serie.channel).lower())

    fname = filetools.join(path, "tvshow.json")
    dict_data = jsontools.load_json(filetools.read(fname))
    
    if not dict_data:
        dict_data = {}

    if filetools.exists(path):
        if create_nfo:
            create_nfo_file(tvshow_id, path, "serie")

    dict_data["active"] = True
    dict_scraper = {"name": scraper, "id": tvshow_id}
    dict_data["scraper"] = dict_scraper
    dict_data["title"] = serie.infoLabels['title']

    # ... añadir canal al registro de la serie
    dict_data["channel"] = serie.channel
    dict_data["show"] = serie.show.strip()
    dict_data["url"] = serie.url
    dict_data["path"] = path

    json_data = jsontools.dump_json(dict_data)
    filetools.write(filetools.join(path, "tvshow.json"), json_data)


def mark_as_watched(category, video_id=0):
    """
    marca el capitulo como visto en la libreria de Kodi
    @type category: str
    @param category: categoria "Series" o "Cine"
    @type video_id: int
    @param video_id: identificador 'episodeid' o 'movieid' en la BBDD
    """
    logger.info("pelisalacarta.platformcode.library mark_as_watched - category:{0}".format(category))

    logger.info("se espera 5 segundos por si falla al reproducir el fichero")
    xbmc.sleep(5000)

    if not is_compatible() or not config.get_setting("mark_as_watched") == "true":
        return

    if xbmc.Player().isPlaying():
        payload = {"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}
        data = get_data(payload)

        if 'result' in data:
            payload_f = ''
            player_id = data['result'][0]["playerid"]

            if category == "Series":
                episodeid = video_id
                if episodeid == 0:
                    payload = {"jsonrpc": "2.0", "params": {"playerid": player_id,
                                                            "properties": ["season", "episode", "file", "showtitle"]},
                               "method": "Player.GetItem", "id": "libGetItem"}

                    data = get_data(payload)
                    if 'result' in data:
                        season = data['result']['item']['season']
                        episode = data['result']['item']['episode']
                        showtitle = data['result']['item']['showtitle']
                        # logger.info("titulo es {0}".format(showtitle))

                        payload = {
                            "jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes",
                            "params": {
                                "filter": {"and": [{"field": "season", "operator": "is", "value": str(season)},
                                                   {"field": "episode", "operator": "is", "value": str(episode)}]},
                                "properties": ["title", "plot", "votes", "rating", "writer", "firstaired", "playcount",
                                               "runtime", "director", "productioncode", "season", "episode",
                                               "originaltitle", "showtitle", "lastplayed", "fanart", "thumbnail",
                                               "file", "resume", "tvshowid", "dateadded", "uniqueid"]},
                            "id": 1}

                        data = get_data(payload)
                        if 'result' in data:
                            for d in data['result']['episodes']:
                                if d['showtitle'] == showtitle:
                                    episodeid = d['episodeid']
                                    break

                if episodeid != 0:
                    payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {
                        "episodeid": episodeid, "playcount": 1}, "id": 1}

            else:  # Categoria == 'Movies'
                movieid = video_id
                if movieid == 0:

                    payload = {"jsonrpc": "2.0", "method": "Player.GetItem",
                               "params": {"playerid": 1,
                                          "properties": ["year", "file", "title", "uniqueid", "originaltitle"]},
                               "id": "libGetItem"}

                    data = get_data(payload)
                    logger.debug(repr(data))
                    if 'result' in data:
                        title = data['result']['item']['title']
                        year = data['result']['item']['year']
                        # logger.info("titulo es {0}".format(title))

                        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies",
                                   "params": {
                                       "filter": {"and": [{"field": "title", "operator": "is", "value": title},
                                                          {"field": "year", "operator": "is", "value": str(year)}]},
                                       "properties": ["title", "plot", "votes", "rating", "writer", "playcount",
                                                      "runtime", "director", "originaltitle", "lastplayed", "fanart",
                                                      "thumbnail", "file", "resume", "dateadded"]},
                                   "id": 1}

                        data = get_data(payload)

                        if 'result' in data:
                            for d in data['result']['movies']:
                                logger.info("title {0}".format(d['title']))
                                if d['title'] == title:
                                    movieid = d['movieid']
                                    break

                if movieid != 0:
                    payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {
                        "movieid": movieid, "playcount": 1}, "id": 1}

            if payload_f:
                condicion = int(config.get_setting("watched_setting"))
                payload = {"jsonrpc": "2.0", "method": "Player.GetProperties",
                           "params": {"playerid": player_id,
                                      "properties": ["time", "totaltime", "percentage"]},
                           "id": 1}

                while xbmc.Player().isPlaying():
                    data = get_data(payload)
                    # logger.debug("Player.GetProperties: {0}".format(data))
                    # 'result': {'totaltime': {'hours': 0, 'seconds': 13, 'minutes': 41, 'milliseconds': 341},
                    #            'percentage': 0.209716334939003,
                    #            'time': {'hours': 0, 'seconds': 5, 'minutes': 0, 'milliseconds': 187}}

                    if 'result' in data:
                        from datetime import timedelta
                        totaltime = data['result']['totaltime']
                        totaltime = totaltime['seconds'] + 60 * totaltime['minutes'] + 3600 * totaltime['hours']
                        tiempo_actual = data['result']['time']
                        tiempo_actual = timedelta(hours=tiempo_actual['hours'], minutes=tiempo_actual['minutes'],
                                                  seconds=tiempo_actual['seconds'])

                        if condicion == 0:  # '5 minutos'
                            mark_time = timedelta(seconds=300)
                        elif condicion == 1:  # '30%'
                            mark_time = timedelta(seconds=totaltime * 0.3)
                        elif condicion == 2:  # '50%'
                            mark_time = timedelta(seconds=totaltime * 0.5)
                        elif condicion == 3:  # '80%'
                            mark_time = timedelta(seconds=totaltime * 0.8)

                        logger.debug(str(mark_time))

                        if tiempo_actual > mark_time:
                            # Marcar como visto
                            data = get_data(payload_f)
                            if data['result'] != 'OK':
                                logger.info("ERROR al poner el contenido como visto")
                            break

                    xbmc.sleep(30000)


def get_data(payload):
    """
    obtiene la información de la llamada JSON-RPC con la información pasada en payload
    @type payload: dict
    @param payload: data
    :return:
    """
    logger.info("pelisalacarta.platformcode.library get_data:: payload {0}".format(payload))
    # Required header for XBMC JSON-RPC calls, otherwise you'll get a 415 HTTP response code - Unsupported media type
    headers = {'content-type': 'application/json'}

    if modo_cliente:
        try:
            req = urllib2.Request(xbmc_json_rpc_url, data=jsontools.dump_json(payload), headers=headers)
            f = urllib2.urlopen(req)
            response = f.read()
            f.close()

            logger.info("pelisalacarta.platformcode.library get_data:: response {0}".format(response))
            data = jsontools.load_json(response)
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("pelisalacarta.platformcode.library get_data:: error en xbmc_json_rpc_url: {0}".format(message))
            data = ["error"]
    else:
        try:
            data = jsontools.load_json(xbmc.executeJSONRPC(jsontools.dump_json(payload)))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("pelisalacarta.platformcode.library get_data:: error en xbmc.executeJSONRPC: {0}".format(message))
            data = ["error"]

    logger.info("pelisalacarta.platformcode.library get_data:: data {0}".format(data))

    return data


def check_tvshow_xml():
    logger.info("pelisalacarta.platformcode.library check_tvshow_xml")
    fname = filetools.join(config.get_data_path(), TVSHOW_FILE_OLD)
    flag = True

    if not filetools.exists(fname):
        flag = False
    else:
        data = filetools.read(fname)
        if data == "":
            flag = False

    if flag:
        upgrade_library()


def upgrade_library():
    logger.info("pelisalacarta.platformcode.library upgrade_library")
    platformtools.dialog_ok("Biblioteca: Se va a actualizar al nuevo formato",
                            "Seleccione el nombre correcto de cada serie, si no está seguro pulse 'Cancelar'.",
                            "Hay nuevas opciones en 'Biblioteca' y en la 'configuración' del addon.")

    if filetools.exists(TVSHOWS_PATH):
        filetools.rename(TVSHOWS_PATH, os.path.join(config.get_library_path(), "SERIES_OLD"))

    if not filetools.exists(TVSHOWS_PATH):

        filetools.mkdir(TVSHOWS_PATH)
        if filetools.exists(TVSHOWS_PATH):
            fname = filetools.join(config.get_data_path(), TVSHOW_FILE_OLD)

            if filetools.exists(fname):
                try:
                    with open(fname, "r") as f:
                        for line in f:
                            aux = line.rstrip('\n').split(",")
                            tvshow = aux[0].strip()
                            url = aux[1].strip()
                            channel = aux[2].strip()

                            serie = Item()
                            serie.infoLabels = {}

                            patron = "^(.+)[\s]\((\d{4})\)$"
                            matches = re.compile(patron, re.DOTALL).findall(tvshow)

                            if matches:
                                serie.infoLabels['title'] = matches[0][0]
                                serie.infoLabels['year'] = matches[0][1]
                            else:
                                serie.infoLabels['title'] = tvshow

                            create_nfo = False

                            # TODO de momento es el unico, cuando haya más se podrá configurar
                            scraper = "tmdb"

                            # Abrir ventana de seleccion para identificar la serie
                            serie = get_video_id_from_scraper(serie, True, scraper=scraper)

                            if scraper == "tmdb":
                                scrape_id = "id_Tmdb"

                            if scrape_id in serie.infoLabels:
                                tvshow_id = serie.infoLabels[scrape_id]
                                create_nfo = True
                            else:
                                tvshow_id = "t_{0}_[{1}]".format(tvshow.strip().replace(" ", "_"), channel)

                            path = filetools.join(TVSHOWS_PATH, filetools.title_to_filename("{0} [{1}]".format(
                                tvshow.strip().lower(), channel)))

                            logger.info("pelisalacarta.platformcode.library upgrade_library Creando directorio serie:" +
                                        path)
                            try:
                                filetools.mkdir(path)
                                if create_nfo:
                                    create_nfo_file(tvshow_id, path, "serie")

                            except OSError as exception:
                                if exception.errno != errno.EEXIST:
                                    raise

                            dict_data = dict()
                            dict_data["active"] = True
                            dict_scraper = {"name": scraper, "id": tvshow_id}
                            dict_data["scraper"] = dict_scraper
                            dict_data["title"] = serie.infoLabels['title']

                            # ... añadir canal al registro de la serie
                            dict_data["channel"] = channel
                            dict_data["show"] = tvshow
                            dict_data["url"] = url
                            dict_data["path"] = path

                            json_data = jsontools.dump_json(dict_data)
                            filetools.write(filetools.join(path, "tvshow.json"), json_data)

                except EnvironmentError:
                    logger.info("ERROR al leer el archivo: {0}".format(fname))
                else:
                    filetools.rename(filetools.join(config.get_data_path(), TVSHOW_FILE_OLD),
                                     filetools.join(config.get_data_path(), "series_old.xml"))

        else:
            logger.info("ERROR, no se ha podido crear la nueva carpeta de SERIES")
    else:
        logger.info("ERROR, no se ha podido renombrar la antigua carpeta de SERIES")


def update():
    """
    actualiza la libreria
    """
    logger.info("pelisalacarta.platformcode.library update")
    # Se comenta la llamada normal para reutilizar 'payload' dependiendo del modo cliente
    # xbmc.executebuiltin('UpdateLibrary(video)')
    payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "id": 1}
    data = get_data(payload)
    logger.info("pelisalacarta.platformcode.library update data:{0}".format(data))


def create_nfo_file(video_id, path, type_video):
    """
    crea el fichero nfo con la información para scrapear la pelicula o serie
    @type video_id: str
    @param video_id: codigo identificativo del video
    @type path: str
    @param path: ruta donde se creará el fichero
    @type type_video: str
    @param type_video: tipo de video "serie" o "pelicula"
    """
    # TODO meter un parametro más "scraper" para elegir entre una lista: imdb, tvdb, etc... y con el video_id pasado de
    # esa pagina se genere el nfo especifico
    logger.info("pelisalacarta.platformcode.library create_nfo_file")

    if type_video == "serie":
        data = "https://www.themoviedb.org/tv/{0}".format(video_id)
        nfo_file = filetools.join(path, "tvshow.nfo")
    else:
        data = "https://www.themoviedb.org/movie/{0}".format(video_id)
        nfo_file = path + ".nfo"

    filetools.write(nfo_file, data)


def add_pelicula_to_library(item):
    logger.info("pelisalacarta.platformcode.launcher add_pelicula_to_library")

    new_item = item.clone(action="play_from_library", category="Cine")
    insertados, sobreescritos, fallidos = save_library_movie(new_item)

    if fallidos == 0:
        platformtools.dialog_ok("Biblioteca", "La pelicula se ha añadido a la biblioteca")
    else:
        platformtools.dialog_ok("Biblioteca", "ERROR, la pelicula NO se ha añadido a la biblioteca")

    # library.update()


def add_serie_to_library(item, channel):
    logger.info("pelisalacarta.platformcode.launcher add_serie_to_library, show=#"+item.show+"#")

    # Esta marca es porque el item tiene algo más aparte en el atributo "extra"
    item.action = item.extra
    if "###" in item.extra:
        item.action = item.extra.split("###")[0]
        item.extra = item.extra.split("###")[1]

    # Obtiene el listado desde el que se llamó
    itemlist = getattr(channel, item.action)(item)

    insertados, sobreescritos, fallidos = save_library_tvshow(item, itemlist)

    if fallidos > -1 and (insertados + sobreescritos) > 0:
        # Guardar el registro tvshow.json
        save_tvshow_json(item)

    if fallidos == -1:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido a la biblioteca")
        logger.error("La serie {0} no se ha podido añadir a la biblioteca".format(item.show))

    elif fallidos > 0:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido completa a la biblioteca")
        logger.error("No se han podido añadir {0} episodios de la serie {1} a la biblioteca".format(fallidos,
                                                                                                    item.show))
    else:
        platformtools.dialog_ok("Biblioteca", "La serie se ha añadido a la biblioteca")
        logger.info("[launcher.py] Se han añadido {0} episodios de la serie {1} a la biblioteca".format(insertados,
                                                                                                        item.show))
    # library.update() # TODO evitar bucle
