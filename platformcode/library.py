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
import sys
import urllib
import urllib2
from threading import Thread

import xbmc
from core import config
from core import filetools
from core import jsontools
from core import logger
from core import scrapertools
try:
    from core import tmdb
except ImportError:
    tmdb = None
from core.item import Item
from platformcode import platformtools

addon_name = sys.argv[0].strip()
if not addon_name or addon_name.startswith("default.py"):
    addon_name = "plugin://plugin.video.pelisalacarta/"

modo_cliente = int(config.get_setting("library_mode"))
# Host name where XBMC is running, leave as localhost if on this PC
# Make sure "Allow control of XBMC via HTTP" is set to ON in Settings ->
# Services -> Webserver
xbmc_host = config.get_setting("xbmc_host")
# Configured in Settings -> Services -> Webserver -> Port
xbmc_port = int(config.get_setting("xbmc_port"))
# Base URL of the json RPC calls. For GET calls we append a "request" URI
# parameter. For POSTs, we add the payload as JSON the the HTTP request body
xbmc_json_rpc_url = "http://"+xbmc_host+":"+str(xbmc_port)+"/jsonrpc"

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
    filetools.mkdir(MOVIES_PATH)

FOLDER_TVSHOWS = "SERIES"  # config.get_localized_string(30073)
TVSHOWS_PATH = filetools.join(LIBRARY_PATH, FOLDER_TVSHOWS)
if not filetools.exists(TVSHOWS_PATH):
    logger.info("pelisalacarta.platformcode.library Tvshows path doesn't exist:" + TVSHOWS_PATH)
    filetools.mkdir(TVSHOWS_PATH)

TVSHOW_FILE = "series.json"
TVSHOW_FILE_OLD = "series.xml"

otmdb = None


def is_compatible():
    """
    comprueba si la plataforma es xbmc/Kodi, la version es compatible y si está configurada la libreria en Kodi.
    @rtype:   bool
    @return:  si es compatible.

    """
    logger.info("pelisalacarta.platformcode.library is_compatible")
    # Versions compatible with JSONRPC v6 (frodo en adelante).
    # config.OLD_PLATFORM son todas las versiones de frodo hacia abajo.
    # Si hemos dicho que nos busque la información de Kodi, damos por supuesto que está configurada su biblioteca
    if not config.OLD_PLATFORM and config.get_setting("get_metadata_from_kodi") == "true":
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
    logger.info("pelisalacarta.platformcode.library save_library_movie")
    # logger.debug(item.tostring('\n'))
    insertados = 0
    sobreescritos = 0
    fallidos = 0

    # Itentamos obtener el titulo correcto:
    # 1. contentTitle: Este deberia ser el sitio correcto, ya que title suele contener "Añadir a la biblioteca..."
    # 2. fulltitle
    # 3. title
    if not item.contentTitle:
        # Colocamos el titulo correcto en su sitio para que tmdb lo localize
        if item.fulltitle:
            item.contentTitle = item.fulltitle
        else:
            item.contentTitle = item.title

    # Si llegados a este punto no tenemos titulo, salimos
    if not item.contentTitle or not item.channel:
        return 0, 0, -1  # Salimos sin guardar

    # TODO configurar para segun el scraper se llamara a uno u otro
    tmdb_return = tmdb.find_and_set_infoLabels_tmdb(item, config.get_setting("scrap_ask_name") == "true")

    # Llegados a este punto podemos tener:
    #  tmdb_return = True: Un item con infoLabels con la información actualizada de la peli
    #  tmdb_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    if not tmdb_return:
        # TODO de momento si no hay resultado no añadimos nada, aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        return 0, 0, -1

    # progress dialog
    p_dialog = platformtools.dialog_progress('pelisalacarta', 'Añadiendo película...')

    #  TODO utilizar contentTitle pero hay asegurarse q base_name es un filename correcto
    base_name = filter(lambda c: c not in ":*?<>|\/", item.contentTitle).strip().lower()
    path = filetools.join(MOVIES_PATH, "%s [%s]" %(base_name, item.infoLabels['tmdb_id']))
    if not filetools.exists(path):
        logger.info("pelisalacarta.platformcode.library save_library_movie Creando directorio pelicula:" + path)
        try:
            filetools.mkdir(path)
        except OSError, exception:
            if exception.errno != errno.EEXIST:
                raise


    # Crear base_name.strm con un item para ir a get_canales si no existe
    strm_path = filetools.join(path, "%s.strm" %base_name)
    nfo_path = filetools.join(path, "%s.nfo" % base_name)
    if not filetools.exists(strm_path):
        item_strm = item.clone(action='play_from_library', channel='biblioteca', path= path,
                               infoLabels={'title': item.contentTitle})

        if filetools.write(strm_path, '%s?%s' %(addon_name, item_strm.tourl())):
            # Crear base_name.nfo si no existe con la url_scraper, info de la pelicula y marcas de vista
            if not filetools.exists(nfo_path):
                url_scraper = "https://www.themoviedb.org/movie/%s\n" %item.infoLabels['tmdb_id']
                item.library_playcounts = {base_name: 0}

                if not filetools.write(nfo_path, url_scraper + item.tojson()):
                    # Si no se puede crear base_name.nfo borramos base_name.strm
                    filetools.remove(strm_path)


    # Solo si existen base_name.nfo y base_name.strm continuamos
    if filetools.exists(nfo_path) and filetools.exists(strm_path):
        json_path = filetools.join(path, ("%s [%s].json" %(base_name, item.channel)).lower())
        if filetools.exists(json_path):
            logger.info("pelisalacarta.platformcode.library savelibrary el fichero existe. Se sobreescribe")
            sobreescritos += 1
        else:
            insertados += 1

        if filetools.write(json_path, '%s?%s' % (addon_name, item.clone(infoLabels={}).tojson())):
            p_dialog.update(100, 'Añadiendo película...', item.contentTitle)
            p_dialog.close()

            # actualizamos la biblioteca de Kodi con la pelicula
            # TODO arreglar el porque hay que poner la ruta special
            ruta = "special://home/userdata/addon_data/plugin.video.pelisalacarta/library/CINE/"
            update(ruta)

            return insertados, sobreescritos, fallidos

    # Si llegamos a este punto es por q algo ha fallado
    logger.error("No se ha podido guardar %s en la biblioteca" % item.contentTitle)
    p_dialog.update(100, 'Fallo al añadir...', item.contentTitle)
    p_dialog.close()
    # TODO habria q poner otra advertencia?
    return 0, 0, -1


def save_library_tvshow(item, episodelist):
    """
    guarda en la libreria de series la serie con todos los capitulos incluidos en la lista episodelist
    @type item: item
    @param item: item que representa la serie a guardar
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos o -1 si ha fallado toda la serie
    """
    logger.info("pelisalacarta.platformcode.library save_library_tvshow")
    # logger.debug(item.tostring('\n'))

    # Itentamos obtener el titulo correcto:
    # 1. contentSerieName: Este deberia ser el sitio correcto
    # 2. show
    if not item.contentSerieName:
        # Colocamos el titulo en su sitio para que tmdb lo localize
        item.contentSerieName = item.show

    # establecemos "active" para que se actualice cuando se llame a library_service
    item.active = True

    # Si llegados a este punto no tenemos titulo, salimos
    if not item.contentSerieName or not item.channel:
        return 0, 0, -1  # Salimos sin guardar

    # TODO configurar para segun el scraper se llame a uno u otro
    tmdb_return = tmdb.find_and_set_infoLabels_tmdb(item, config.get_setting("scrap_ask_name") == "true")

    # Llegados a este punto podemos tener:
    #  tmdb_return = True: Un item con infoLabels con la información actualizada de la serie
    #  tmdb_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    if not tmdb_return:
        # TODO de momento si no hay resultado no añadimos nada, aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        return 0, 0, -1

    #  TODO utilizar contentSerieName pero hay asegurarse q base_name es un filename correcto
    base_name = filter(lambda c: c not in ":*?<>|\/", item.contentSerieName).strip().lower()
    path = filetools.join(TVSHOWS_PATH, ("%s [%s]" %(base_name, item.infoLabels['tmdb_id'])))
    if not filetools.exists(path):
        logger.info("pelisalacarta.platformcode.library save_library_tvshow Creando directorio serie:" + path)
        try:
            filetools.mkdir(path)
        except OSError, exception:
            if exception.errno != errno.EEXIST:
                raise

    tvshow_path = filetools.join(path, "tvshow.nfo")
    if not filetools.exists(tvshow_path):
        # Creamos tvshow.nfo, si no existe, con la url_scraper, info de la serie y marcas de episodios vistos
        logger.info("pelisalacarta.platformcode.library save_library_tvshow Creando tvshow.nfo:" + tvshow_path)
        url_scraper = "https://www.themoviedb.org/tv/%s\n" % item.infoLabels['tmdb_id']
        item_tvshow = item.clone()
        item_tvshow.library_playcounts = {}
        item_tvshow.library_urls = {item.channel: item.url}
        item_tvshow.title = item_tvshow.contentTitle
        item_tvshow.channel = "biblioteca"
        item_tvshow.fanart = item_tvshow.infoLabels['fanart']
        item_tvshow.path = path
        item_tvshow.url =""

        filetools.write(tvshow_path, url_scraper + item_tvshow.tojson())

    else:
        # Si existe tvshow.nfo, pero estamos añadiendo un nuevo canal actualizamos el listado de urls
        url_scraper = filetools.read(tvshow_path, 0, 1)
        tvshow_item = Item().fromjson(filetools.read(tvshow_path, 1))
        if item.channel not in tvshow_item.library_urls:
            tvshow_item.library_urls[item.channel] = item.url
            filetools.write(tvshow_path, url_scraper + tvshow_item.tojson())



    # Guardar los episodios
    insertados, sobreescritos, fallidos = save_library_episodes(path, episodelist, item)

    #TODO si fallidos == -1 podriamos comprobar si es necesario eliminar la serie



    return insertados, sobreescritos, fallidos


def save_library_episodes(path, episodelist, serie, silent=False, overwrite= True):
    """
    guarda en la ruta indicada todos los capitulos incluidos en la lista episodelist
    @type path: str
    @param path: ruta donde guardar los episodios
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @type serie: item
    @param serie: serie de la que se van a guardar los episodios
    @type silent: bool
    @param silent: establece si se muestra la notificación
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos
    """
    logger.info("pelisalacarta.platformcode.library save_library_episodes")

    # No hay lista de episodios, no hay nada que guardar
    if not len(episodelist):
        logger.info("pelisalacarta.platformcode.library save_library_episodes No hay lista de episodios, "
                    "salimos sin crear strm")
        return 0, 0, 0

    insertados = 0
    sobreescritos = 0
    fallidos = 0
    news_in_playcounts= {}

    # Silent es para no mostrar progreso (para library_service)
    if not silent:
        # progress dialog
        p_dialog = platformtools.dialog_progress('pelisalacarta', 'Añadiendo episodios...')
        p_dialog.update(0, 'Añadiendo episodio...')

    # fix float porque la division se hace mal en python 2.x
    t = float(100) / len(episodelist)

    for i, e in enumerate(episodelist):
        if not silent:
            p_dialog.update(int(math.ceil((i+1) * t)), 'Añadiendo episodio...', e.title)

        # Añade todos menos el que dice "Añadir esta serie..." o "Descargar esta serie..."
        if e.action == "add_serie_to_library" or e.action == "download_all_episodes":
            continue

        season_episode = scrapertools.get_season_and_episode(e.title.lower())
        e.infoLabels = serie.infoLabels
        e.contentSeason, e.contentEpisodeNumber = season_episode.split("x")

        strm_path = filetools.join(path, "%s.strm" % season_episode)
        if not filetools.exists(strm_path):
            # Si no existe season_episode.strm añadirlo
            item_strm = e.clone(action='play_from_library', channel='biblioteca', path=path, infoLabels={})
            item_strm.contentSeason = e.contentSeason
            item_strm.contentEpisodeNumber = e.contentEpisodeNumber
            item_strm.contentType = e.contentType
            item_strm.contentTitle = "%sx%s" %(e.contentSeason, str(e.contentEpisodeNumber).zfill(2))
            logger.debug(item_strm.tostring('\n'))

            filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))

        nfo_path = filetools.join(path, "%s.nfo" % season_episode)
        if not filetools.exists(nfo_path) and e.infoLabels.get("tmdb_id"):
            # Si no existe season_episode.nfo añadirlo
            tmdb.find_and_set_infoLabels_tmdb(e, config.get_setting("scrap_ask_name") == "true")
            item_nfo = e.clone()
            url_scraper = "https://www.themoviedb.org/tv/%s/season/%s/episode/%s\n" %(item_nfo.infoLabels['tmdb_id'],
                            item_nfo.contentSeason, item_nfo.contentEpisodeNumber)
            filetools.write(nfo_path, url_scraper + item_nfo.tojson())

        # Solo si existen season_episode.nfo y season_episode.strm continuamos
        json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())
        if filetools.exists(nfo_path) and filetools.exists(strm_path):
            nuevo = not filetools.exists(json_path)

            if nuevo or overwrite:
                #if filetools.write(json_path, '%s?%s' % (addon_name, e.tojson())):
                if filetools.write(json_path, e.tojson()): #TODO si funciona hacerlo en cine tb
                    if nuevo:
                        logger.info("pelisalacarta.platformcode.library savelibrary Insertado: %s" % json_path)
                        insertados += 1
                        # Marcamos episodio como no visto
                        news_in_playcounts[season_episode] = 0
                        # Marcamos la temporada como no vista
                        news_in_playcounts["season %s" % e.contentSeason] = 0
                    else:
                        logger.info("pelisalacarta.platformcode.library savelibrary Sobreescrito: %s" % json_path)
                        sobreescritos += 1
                else:
                    logger.info("pelisalacarta.platformcode.library savelibrary Fallido: %s" % json_path)
                    fallidos += 1

        else:
            logger.info("pelisalacarta.platformcode.library savelibrary Fallido: %s" % json_path)
            fallidos += 1

        if not silent and p_dialog.iscanceled():
            break

    if not silent:
        p_dialog.close()

    if news_in_playcounts:
        # Si hay nuevos episodios los marcamos como no vistos en tvshow.nfo ...
        tvshow_path = filetools.join(path, "tvshow.nfo")
        try:
            url_scraper =filetools.read(tvshow_path,0,1)
            tvshow_item = Item().fromjson(filetools.read(tvshow_path,1))
            tvshow_item.library_playcounts.update(news_in_playcounts)

            filetools.write(tvshow_path, url_scraper + tvshow_item.tojson())
        except:
            logger.error("Error al actualizar tvshow.nfo")
            fallidos = -1

        # ... y actualizamos la biblioteca de Kodi
        # TODO arreglar el porque hay que poner la ruta special
        ruta = "special://home/userdata/addon_data/plugin.video.pelisalacarta/library/SERIES/" + \
               os.path.basename(path) + "/"
        logger.debug(ruta)
        update(ruta)

    if fallidos == len(episodelist):
        fallidos = -1

    logger.debug("%s [%s]: insertados= %s, sobreescritos= %s, fallidos= %s" %(serie.contentSerieName, serie.channel, insertados, sobreescritos, fallidos))
    return insertados, sobreescritos, fallidos

'''
def set_infolabels_from_library(itemlist, tipo):
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

    # Metodo 1: De la bilioteca de pelisalacarta
    if tipo == 'Movies':
        for item in itemlist:
            data_file = os.path.splitext(item.path)[0] + ".nfo"
            if filetools.exists(data_file):
                it = Item().fromjson(filetools.read(data_file,1))
                item.infoLabels = it.infoLabels
                item.library_playcounts = it.library_playcounts
                item.fanart = item.infoLabels.get('fanart',"")

            item.thumbnail = item.contentThumbnail
            item.title = item.contentTitle

    elif tipo == 'TVShows':
        for item in itemlist:
            data_file = filetools.join(item.path, 'tvshow.nfo')
            if filetools.exists(data_file):
                it = Item().fromjson(filetools.read(data_file,1))
                item.infoLabels = it.infoLabels
                item.library_playcounts = it.library_playcounts
                item.fanart = item.infoLabels.get('fanart', "")

            item.thumbnail = item.contentThumbnail
            item.title = item.contentSerieName

    elif tipo == 'Episodes':
        for item in itemlist:
            data_file = os.path.splitext(item.path)[0] + ".nfo"

            if filetools.exists(data_file):
                data = filetools.read(data_file, 1)
                infoLabels = Item().fromjson(data).infoLabels
                item.infoLabels = infoLabels
                item.fanart = item.infoLabels.get('fanart', "")

            item.thumbnail = item.contentThumbnail
            if item.contentTitle:
                title_episodie = item.contentTitle.strip()
            else:
                title_episodie = "Temporada %s Episodio %s" %(item.contentSeason, str(item.contentEpisodeNumber).zfill(2))

            item.title = "%sx%s - %s" %(item.contentSeason, str(item.contentEpisodeNumber).zfill(2), title_episodie)


    # TODO hay q mirar esto bien
    if config.get_setting("get_metadata_from_kodi") == "true":
        # Metodo2: De la bilioteca de kodi
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
                                                 "playcount", "episode", "imdbnumber", "premiered", "votes",
                                                 "lastplayed", "fanart", "thumbnail", "file", "originaltitle",
                                                 "sorttitle", "episodeguide", "season", "watchedepisodes", "dateadded",
                                                 "tag"]},
                       "id": "libTvShows"}

        elif tipo == 'Episodes' and 'tvshowid' in itemlist[0].infoLabels and itemlist[0].infoLabels['tvshowid']:
            tvshowid = itemlist[0].infoLabels['tvshowid']
            payload = {"jsonrpc": "2.0",
                       "method": "VideoLibrary.GetEpisodes",
                       "params": {"tvshowid": tvshowid,
                                  "properties": ["title", "plot", "votes", "rating", "writer", "firstaired",
                                                 "playcount", "runtime", "director", "productioncode", "season",
                                                 "episode", "originaltitle", "showtitle", "cast", "lastplayed",
                                                 "fanart", "thumbnail", "file", "dateadded", "tvshowid"]},
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

                    if r['file'].endswith(os.sep) or r['file'].endswith('/'):
                        r_filename_aux = r['file'][:-1]
                    else:
                        r_filename_aux = r['file']

                    r_filename = os.path.basename(r_filename_aux)
                    # logger.debug(os.path.basename(i.path) + '\n' + r_filename)
                    i_filename = os.path.basename(i.path)
                    if i_filename == r_filename:
                        infolabels = r

                        # Obtener imagenes y asignarlas al item
                        if 'thumbnail' in infolabels:

                            infolabels['thumbnail'] = urllib.unquote_plus(infolabels['thumbnail']).replace('image://',
                                                                                                           '')
                            if infolabels['thumbnail'].endswith('/'):
                                i.thumbnail = infolabels['thumbnail'][:-1]  
                            else: 
                                i.thumbnail = infolabels['thumbnail']

                        if 'fanart' in infolabels:
                            
                            infolabels['fanart'] = urllib.unquote_plus(infolabels['fanart']).replace('image://', '')
                        
                            if infolabels['fanart'].endswith('/'):
                                i.fanart = infolabels['fanart'][:-1]
                            else:
                                i.fanart = infolabels['fanart']

                        # Adaptar algunos campos al formato infoLables
                        if 'cast' in infolabels:
                            l_castandrole = list()
                            for c in sorted(infolabels['cast'], key=lambda _c: _c["order"]):
                                l_castandrole.append((c['name'], c['role']))
                            infolabels.pop('cast')
                            infolabels['castandrole'] = l_castandrole
                        if 'genre' in infolabels:
                            infolabels['genre'] = ', '.join(infolabels['genre'])
                        if 'writer' in infolabels:
                            infolabels['writer'] = ', '.join(infolabels['writer'])
                        if 'director' in infolabels:
                            infolabels['director'] = ', '.join(infolabels['director'])
                        if 'country' in infolabels:
                            infolabels['country'] = ', '.join(infolabels['country'])
                        if 'studio' in infolabels:
                            infolabels['studio'] = ', '.join(infolabels['studio'])
                        if 'runtime' in infolabels:
                            infolabels['duration'] = infolabels.pop('runtime')

                        # Fijar el titulo si existe y añadir infoLabels al item
                        if 'label' in infolabels:
                            i.title = infolabels['label']
                        i.infoLabels = infolabels
                        result.remove(r)
                        break
'''

def mark_as_watched(item):
    Thread(target=mark_as_watched_on_strm, args=[item]).start()
    Thread(target=mark_as_watched_on_kodi, args=[item]).start()


def mark_as_watched_on_strm(item):
    """
    Marca un .strm como "visto" añadiendo el parametro "playcount" a los infoLabels del strm.
    @param item: item que queremos marcar como visto
    @type item: item
    """
    logger.info("pelisalacarta.platformcode.library mark_as_watched_on_strm")
    if not config.get_setting("mark_as_watched") == "true":
        return

    xbmc.sleep(5000)

    while xbmc.Player().isPlaying():
        tiempo_actual = xbmc.Player().getTime()
        totaltime = xbmc.Player().getTotalTime()
        condicion = int(config.get_setting("watched_setting"))

        if condicion == 0:  # '5 minutos'
            mark_time = 300 #TODO son 300000
        elif condicion == 1:  # '30%'
            mark_time = totaltime * 0.3
        elif condicion == 2:  # '50%'
            mark_time = totaltime * 0.5
        elif condicion == 3:  # '80%'
            mark_time = totaltime * 0.8

        logger.debug(str(mark_time))

        if tiempo_actual > mark_time:
            f = filetools.join(os.path.dirname(item.path), 'tvshow.nfo')
            if not filetools.exists(f):
                # No es una serie, probamos si es un pelicula
                f = os.path.splitext(item.path)[0] + '.nfo'
                if not filetools.exists(f):
                    # Fichero nfo no encontrado
                    break

            url_scraper = data[filetools.read(f, 0, 1)]
            it = Item().fromjson(filetools.read(f, 1))
            name_file =  os.path.splitext(os.path.basename(item.path))[0]
            if not hasattr(it, 'library_playcounts'): it.library_playcounts = {}
            it.library_playcounts.update({name_file: 1})

            filetools.write(f, url_scraper + it.tojson())

        xbmc.sleep(30000)


def mark_as_watched_on_kodi(item):
    """
    marca el capitulo como visto en la libreria de Kodi
    @type item: item
    @param item: elemento a marcar como visto
    """
    logger.info("pelisalacarta.platformcode.library mark_as_watched_on_kodi")
    # logger.info("item mark_as_watched_on_kodi {}".format(item.tostring()))
    video_id = 0
    category = ''
    if 'infoLabels' in item:
        if 'episodeid' in item.infoLabels and item.infoLabels['episodeid']:
            category = 'Series'
            video_id = item.infoLabels['episodeid']

        elif 'movieid' in item.infoLabels and item.infoLabels['movieid']:
            category = 'Movies'
            video_id = item.infoLabels['movieid']

        else:
            if hasattr(item, "show") or hasattr(item, "contentSerieName"):
                category = 'Series'

    else:
        if hasattr(item, "show") or hasattr(item, "contentSerieName"):
            category = 'Series'

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
        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("pelisalacarta.platformcode.library get_data:: error en xbmc_json_rpc_url: {0}".format(message))
            data = ["error"]
    else:
        try:
            data = jsontools.load_json(xbmc.executeJSONRPC(jsontools.dump_json(payload)))
        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("pelisalacarta.platformcode.library get_data:: error en xbmc.executeJSONRPC: {0}".
                        format(message))
            data = ["error"]

    logger.info("pelisalacarta.platformcode.library get_data:: data {0}".format(data))

    return data


def update(_path):
    """
    actualiza la libreria

    @type _path: str
    @param _path: ruta que hay que actualizar en la libreria
    """
    logger.info("pelisalacarta.platformcode.library update")
    # Se comenta la llamada normal para reutilizar 'payload' dependiendo del modo cliente
    # xbmc.executebuiltin('UpdateLibrary(video)')
    if _path:
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "params": {"directory": _path}, "id": 1}
    else:
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "id": 1}
    data = get_data(payload)
    logger.info("pelisalacarta.platformcode.library update data:{0}".format(data))


def clean(mostrar_dialogo=False):
    """
    limpia la libreria de elementos que no existen
    @param mostrar_dialogo: muestra el cuadro de progreso mientras se limpia la biblioteca
    @type mostrar_dialogo: bool
    """
    logger.info("pelisalacarta.platformcode.library clean")
    if mostrar_dialogo:
        dialog = "true"
    else:
        dialog = "false"

    # TODO pendiente arreglar showdialogs
    payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Clean", "id": 1}  #, "showdialogs": dialog}
    data = get_data(payload)
    logger.info("pelisalacarta.platformcode.library clean data:{0}".format(data))

'''
def create_nfo_file(item, video_id, path, content_type):
    """
    crea el fichero nfo con la información para scrapear la pelicula o serie
    @type item: Item
    @param item: elemento que se va a guardar
    @type video_id: str
    @param video_id: codigo identificativo del video
    @type path: str
    @param path: ruta donde se creará el fichero
    @type content_type: str
    @param content_type: tipo de video "TVShows", "Episodes" o "Movies"
    """
    # TODO meter un parametro más "scraper" para elegir entre una lista: imdb, tvdb, etc... y con el video_id pasado de
    # esa pagina se genere el nfo especifico
    logger.info("pelisalacarta.platformcode.library create_nfo_file")
    it =item.clone(library_playcounts={})

    if content_type == "TVShows":
        data = "https://www.themoviedb.org/tv/%s\n" %(video_id)
        nfo_file = filetools.join(path, "tvshow.nfo")
        if filetools.exists(nfo_file):
            tvshow_item = Item().fromjson(filetools.read(nfo_file, 1))
            if hasattr(tvshow_item, 'library_playcounts'):
                it.library_playcounts = tvshow_item.library_playcounts

    elif content_type == "Episodes":
        data = "https://www.themoviedb.org/tv/%s/season/%s/episode/%s\n" %(video_id, it.contentSeason, it.contentEpisodeNumber)
        nfo_file = path + ".nfo"

    else: # "Movies"
        data = "https://www.themoviedb.org/movie/%s\n" %(video_id)
        nfo_file = path + ".nfo"
        if filetools.exists(nfo_file):
            movie_item = Item().fromjson(filetools.read(nfo_file, 1))
            if hasattr(movie_item, 'library_playcounts'):
                it.library_playcounts = movie_item.library_playcounts


    data += it.tojson()
    filetools.write(nfo_file, data)
'''

def add_pelicula_to_library(item):
    logger.info("pelisalacarta.platformcode.library add_pelicula_to_library")

    new_item = item.clone(action="findvideos")
    insertados, sobreescritos, fallidos = save_library_movie(new_item)

    if fallidos == 0:
        platformtools.dialog_ok("Biblioteca", "La pelicula se ha añadido a la biblioteca")
    else:
        platformtools.dialog_ok("Biblioteca", "ERROR, la pelicula NO se ha añadido a la biblioteca")


def add_serie_to_library(item, channel):
    logger.info("pelisalacarta.platformcode.library add_serie_to_library, show=#"+item.show+"#")

    # Esta marca es porque el item tiene algo más aparte en el atributo "extra"
    item.action = item.extra
    if "###" in item.extra:
        item.action = item.extra.split("###")[0]
        item.extra = item.extra.split("###")[1]

    if item.from_action:
        item.__dict__["action"] = item.__dict__.pop("from_action")
    if item.from_channel:
        item.__dict__["channel"] = item.__dict__.pop("from_channel")

    # Obtiene el listado desde el que se llamó
    itemlist = getattr(channel, item.action)(item)

    insertados, sobreescritos, fallidos = save_library_tvshow(item, itemlist)

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


# metodos de menu contextual
def marcar_episodio(item): #TODO propongo cambiarle el nombre por q vale para episodios y peliculas
    logger.info("pelisalacarta.platformcode.library marcar_episodio")
    logger.debug("item:\n" + item.tostring('\n'))

    if item.contentType == 'movie':
        f= item.nfo
    else:
        f = filetools.join(item.path, 'tvshow.nfo')

    if filetools.exists(f):
        url_scraper = filetools.read(f, 0, 1)
        it = Item().fromjson(filetools.read(f, 1))
        if not hasattr(it, 'library_playcounts'): it.library_playcounts = {}
        it.library_playcounts[item.contentTitle.lower()] = 1

        filetools.write(f, url_scraper + it.tojson())
        item.infoLabels['playcount'] = 1

        import xbmc
        xbmc.executebuiltin("Container.Refresh") #TODO no parece funcionar hay q salir hasta el menu series/peliculas para actualizar


def marcar_temporada(item):
    logger.info("pelisalacarta.platformcode.library marcar_temporada")

    # Obtener el diccionario de episodios marcados
    f = filetools.join(item.path, 'tvshow.nfo')
    url_scraper = filetools.read(f, 0, 1)
    it = Item().fromjson(filetools.read(f, 1))
    if not hasattr(it, 'library_playcounts'): it.library_playcounts = {}

    # Obtenemos los archivos de los episodios
    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    # Marcamos cada uno de los episodios encontrados de esta temporada
    episodios_marcados = 0
    for i in ficheros:
        if i.endswith(".strm"):
            season, episode = scrapertools.get_season_and_episode(i).split("x")
            if int(season) == int(item.contentSeason):
                name_file = os.path.splitext(os.path.basename(i))[0]
                it.library_playcounts[name_file] = 1
                episodios_marcados += 1


    if episodios_marcados:
        # Añadimos la temporada al diccionario item.library_playcounts
        it.library_playcounts["season %s" %item.contentSeason] = 1

        # Guardamos los cambios en tvshow.nfo
        filetools.write(f, url_scraper + it.tojson())
        item.infoLabels['playcount'] = 1

    return item


def actualizacion_automatica(item):
    logger.info("pelisalacarta.platformcode.library actualizacion_automatica")

    item.action = "episodios"
    item.channel = item.contentChannel
    del item.contentChannel
    filetools.write(filetools.join(item.path, "tvshow.json"), item.tojson())

    import xbmc
    xbmc.executebuiltin("Container.Refresh")


def delete(item):
    logger.info("pelisalacarta.platformcode.library delete")

    if item.contentSerieName or item.show:
        heading = "Eliminar serie"
    else:
        heading = "Eliminar película"

    result = platformtools.dialog_yesno(heading, "¿Realmente desea eliminar '%s'?" % item.infoLabels['title'])

    if result:

        if item.contentSerieName or item.show:
            filetools.rmdirtree(item.path)
        else:
            filetools.remove(item.path)
            filetools.remove(item.path[:-5] + ".nfo")
            # TODO tb se borra aunque no sabemos si se dejara o se quedara la info dentro de nfo
            # filetools.remove(item.path[:-5] + ".strm.json")

        import xbmc
        # esperamos 3 segundos para dar tiempo a borrar los ficheros
        # xbmc.sleep(3000)
        # TODO arreglar no funciona al limpiar en la biblioteca de Kodi
        clean()
        xbmc.executebuiltin("Container.Refresh")
