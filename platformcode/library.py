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

#TVSHOW_FILE = "series.json"
#TVSHOW_FILE_OLD = "series.xml"

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
    path = ""

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
    #  item.infoLabels['imdb_id'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not tmdb_return or not item.infoLabels['imdb_id']:
        # TODO de momento si no hay resultado no añadimos nada, aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        return 0, 0, -1

    id = item.infoLabels['imdb_id']

    # progress dialog
    p_dialog = platformtools.dialog_progress('pelisalacarta', 'Añadiendo película...')

    if item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    else:
        base_name = item.contentTitle

    #  TODO hay q asegurarse q base_name es un filename correcto
    base_name = filter(lambda c: c not in ":*?<>|\/", base_name).strip().lower()

    for raiz, subcarpetas, ficheros in filetools.walk(MOVIES_PATH):
        for c in subcarpetas:
            if c.endswith("[%s]" %id):
                path = filetools.join(raiz, c)
                break

    if not path:
        path = filetools.join(MOVIES_PATH, "%s [%s]" % (base_name, id))
        logger.info("pelisalacarta.platformcode.library save_library_movie Creando directorio pelicula:" + path)
        try:
            filetools.mkdir(path)
        except OSError, exception:
            if exception.errno != errno.EEXIST:
                raise

    # Crear base_name.strm con un item para ir a get_canales si no existe
    strm_path = filetools.join(path, "%s.strm" %base_name)
    nfo_path = filetools.join(path, "%s [%s].nfo" % (base_name, id))
    if not filetools.exists(strm_path):
        item_strm = item.clone(channel='biblioteca', action='play_from_library', strm_path= strm_path.replace(MOVIES_PATH,""),
                               contentType='movie', infoLabels={'title': item.contentTitle})

        if filetools.write(strm_path, '%s?%s' %(addon_name, item_strm.tourl())):
            #filetools.write(strm_path + ".debug", '%s?%s' % (addon_name, item_strm.tojson())) # FOR DEBUG
            # Crear base_name.nfo si no existe con la url_scraper, info de la pelicula y marcas de vista
            if not filetools.exists(nfo_path):
                url_scraper = "https://www.themoviedb.org/movie/%s\n" %item.infoLabels['tmdb_id']
                item_nfo = Item(title = item.contentTitle, channel = "biblioteca", action = 'findvideos',
                                library_playcounts = {"%s [%s]" % (base_name, id): 0}, infoLabels= item.infoLabels,
                                strm_path=strm_path.replace(MOVIES_PATH, ""))

                if not filetools.write(nfo_path, url_scraper + item_nfo.tojson()):
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

        if filetools.write(json_path, item.tojson()):
            p_dialog.update(100, 'Añadiendo película...', item.contentTitle)
            p_dialog.close()

            # actualizamos la biblioteca de Kodi con la pelicula
            # TODO arreglar el porque hay que poner la ruta special
            #ruta = "special://home/userdata/addon_data/plugin.video.pelisalacarta/library/CINE/"
            update()

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
    logger.debug(item.tostring('\n'))
    path = ""

    # Itentamos obtener el titulo correcto:
    # 1. contentSerieName: Este deberia ser el sitio correcto
    # 2. show
    if not item.contentSerieName:
        # Colocamos el titulo en su sitio para que tmdb lo localize
        item.contentSerieName = item.show

    # Si llegados a este punto no tenemos titulo o tmdb_id, salimos
    if not (item.contentSerieName or item.infoLabels['tmdb_id']) or not item.channel:
        return 0, 0, -1  # Salimos sin guardar

    # TODO configurar para segun el scraper se llame a uno u otro
    tmdb_return = tmdb.find_and_set_infoLabels_tmdb(item, config.get_setting("scrap_ask_name") == "true")

    # Llegados a este punto podemos tener:
    #  tmdb_return = True: Un item con infoLabels con la información actualizada de la serie
    #  tmdb_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    #  item.infoLabels['imdb_id'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not tmdb_return or not item.infoLabels['imdb_id']:
        # TODO de momento si no hay resultado no añadimos nada, aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        return 0, 0, -1

    id = item.infoLabels['imdb_id']
    if item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    else:
        base_name = item.contentSerieName

    #  TODO hay q asegurarse q base_name es un filename correcto
    base_name = filter(lambda c: c not in ":*?<>|\/", base_name).strip().lower()

    for raiz, subcarpetas, ficheros in filetools.walk(TVSHOWS_PATH):
        for c in subcarpetas:
            if c.endswith("[%s]" % id):
                path = filetools.join(raiz, c)
                break

    if not path:
        path = filetools.join(TVSHOWS_PATH, ("%s [%s]" %(base_name, id)))
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

        item_tvshow = Item(title = item.contentTitle, channel = "biblioteca", action = "get_temporadas",
                           fanart = item.infoLabels['fanart'], thumbnail= item.infoLabels['thumbnail'],
                           infoLabels = item.infoLabels, path = path.replace(TVSHOWS_PATH,""))
        item_tvshow.active = True # para que se actualice cuando se llame a library_service
        item_tvshow.library_playcounts = {}
        item_tvshow.library_urls = {item.channel: item.url}

        filetools.write(tvshow_path, url_scraper + item_tvshow.tojson())

    else:
        # Si existe tvshow.nfo, pero estamos añadiendo un nuevo canal actualizamos el listado de urls
        url_scraper = filetools.read(tvshow_path, 0, 1)
        tvshow_item = Item().fromjson(filetools.read(tvshow_path, 1))
        tvshow_item.library_urls[item.channel] = item.url
        filetools.write(tvshow_path, url_scraper + tvshow_item.tojson())


    if not episodelist:
        # La lista de episodios esta vacia
        return 0, 0, 0

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
        season_episode = "%sx%s" %(e.contentSeason, str(e.contentEpisodeNumber).zfill(2))

        strm_path = filetools.join(path, "%s.strm" % season_episode)
        if not filetools.exists(strm_path):
            # Si no existe season_episode.strm añadirlo
            item_strm = e.clone(action='play_from_library', channel='biblioteca', strm_path= strm_path.replace(TVSHOWS_PATH,""), infoLabels={})
            item_strm.contentSeason = e.contentSeason
            item_strm.contentEpisodeNumber = e.contentEpisodeNumber
            item_strm.contentType = e.contentType
            item_strm.contentTitle = season_episode
            #logger.debug(item_strm.tostring('\n'))

            filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))
            # filetools.write(strm_path + '.debug', '%s?%s' % (addon_name, item_strm.tojson())) # For debug

        nfo_path = filetools.join(path, "%s.nfo" % season_episode)
        if not filetools.exists(nfo_path) and e.infoLabels.get("tmdb_id"):
            # Si no existe season_episode.nfo añadirlo
            tmdb.find_and_set_infoLabels_tmdb(e, config.get_setting("scrap_ask_name") == "true")
            item_nfo = e.clone(channel="biblioteca", url="",action = 'findvideos', strm_path= strm_path.replace(TVSHOWS_PATH,""))
            url_scraper = "https://www.themoviedb.org/tv/%s/season/%s/episode/%s\n" %(item_nfo.infoLabels['tmdb_id'],
                            item_nfo.contentSeason, item_nfo.contentEpisodeNumber)
            filetools.write(nfo_path, url_scraper + item_nfo.tojson())

        # Solo si existen season_episode.nfo y season_episode.strm continuamos
        json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())
        if filetools.exists(nfo_path) and filetools.exists(strm_path):
            nuevo = not filetools.exists(json_path)

            if nuevo or overwrite:
                if filetools.write(json_path, e.tojson()):
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
        #ruta = "special://home/userdata/addon_data/plugin.video.pelisalacarta/library/SERIES/" + \
        #      os.path.basename(path) + "/"
        #update() # TODO mover a la funcion anterior?

    if fallidos == len(episodelist):
        fallidos = -1

    logger.debug("%s [%s]: insertados= %s, sobreescritos= %s, fallidos= %s" %(serie.contentSerieName, serie.channel, insertados, sobreescritos, fallidos))
    return insertados, sobreescritos, fallidos


def mark_auto_as_watched(item):
    def mark_as_watched_subThread(item):
        logger.info("pelisalacarta.platformcode.library mark_as_watched_subThread")
        #logger.debug("item:\n" + item.tostring('\n'))

        condicion = int(config.get_setting("watched_setting"))

        xbmc.sleep(5000)

        while xbmc.Player().isPlaying():
            tiempo_actual = xbmc.Player().getTime()
            totaltime = xbmc.Player().getTotalTime()

            if condicion == 0:  # '5 minutos'
                mark_time = 300000 #FOR DEBUG = 30
            elif condicion == 1:  # '30%'
                mark_time = totaltime * 0.3
            elif condicion == 2:  # '50%'
                mark_time = totaltime * 0.5
            elif condicion == 3:  # '80%'
                mark_time = totaltime * 0.8

            #logger.debug(str(tiempo_actual))
            #logger.debug(str(mark_time))

            if tiempo_actual > mark_time:
                mark_content_as_watched(item, 1)
                break

            xbmc.sleep(30000)

    # Si esta configurado para marcar como visto
    if config.get_setting("mark_as_watched") == "true":
        Thread(target=mark_as_watched_subThread, args=[item]).start()



def mark_content_as_watched_on_kodi(item, value=1):
    """
    marca el contenido como visto o no visto en la libreria de Kodi
    @type item: item
    @param item: elemento a marcar
    @type value: int
    @param value: >0 para visto, 0 para no visto
    """
    logger.info("pelisalacarta.platformcode.library mark_content_as_watched_on_kodi")
    payload_f = ''

    if item.contentType == "movie":
        movieid = 0
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies",
                   "params": {"properties": ["title", "playcount", "originaltitle", "file"]},
                   "id": 1}

        data = get_data(payload)
        if 'result' in data:
            for d in data['result']['movies']:
                if d['file'].endswith(item.strm_path.replace(MOVIES_PATH,"")):
                    movieid = d['movieid']
                    break

        if movieid != 0:
            payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {
                "movieid": movieid, "playcount": value}, "id": 1}

    else:  # item.contentType != 'movie'
        episodeid = 0
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes",
                    "params": {"properties": ["title", "playcount", "showtitle", "file", "tvshowid"]},
                    "id": 1}

        data = get_data(payload)
        if 'result' in data:
            for d in data['result']['episodes']:
                if d['file'].endswith(item.strm_path.replace(TVSHOWS_PATH,"")):
                    episodeid = d['episodeid']
                    break

        if episodeid != 0:
            payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {
                "episodeid": episodeid, "playcount": value}, "id": 1}


    if payload_f:
        # Marcar como visto
        data = get_data(payload_f)
        #logger.debug(str(data))
        if data['result'] != 'OK':
            logger.error("ERROR al poner el contenido como visto")


def mark_season_as_watched_on_kodi(item, value=1):
    """
        marca toda la temporada como vista o no vista en la libreria de Kodi
        @type item: item
        @param item: elemento a marcar
        @type value: int
        @param value: >0 para visto, 0 para no visto
        """
    logger.info("pelisalacarta.platformcode.library mark_content_as_watched_on_kodi")

    # Solo podemos marcar la temporada como vista en la BBDD de Kodi si la BBDD es local,
    # en caso de compartir BBDD esta funcionalidad no funcionara
    if modo_cliente:
        return

    # Buscamos el nombre de la BBDD de videos
    file_db = ""
    for f in os.listdir(xbmc.translatePath("special://userdata/Database")):
        path_f = os.path.join(xbmc.translatePath("special://userdata/Database"), f)

        if os.path.isfile(path_f) and f.lower().startswith('myvideos') and f.lower().endswith('.db'):
            file_db = path_f
            break

    if file_db:
        import sqlite3
        conn = sqlite3.connect(file_db)
        cur = conn.cursor()
        item_path = "%" + item.path.replace("\\\\","\\").replace(TVSHOWS_PATH,"")
        if item_path[:-1] != "\\":
            item_path += "\\"
        sql = 'update files set playCount= %s where idFile  in ' \
              '(select idfile from episode_view where strPath like "%s" and c12= %s)' %\
              (value, item_path, item.contentSeason)
        #logger.debug(sql)
        cur.execute(sql)
        conn.commit()
        cur.close()


def get_data(payload):
    """
    obtiene la información de la llamada JSON-RPC con la información pasada en payload
    @type payload: dict
    @param payload: data
    :return:
    """
    logger.info("pelisalacarta.platformcode.library get_data: payload %s" %payload)
    # Required header for XBMC JSON-RPC calls, otherwise you'll get a 415 HTTP response code - Unsupported media type
    headers = {'content-type': 'application/json'}

    if modo_cliente:
        try:
            req = urllib2.Request(xbmc_json_rpc_url, data=jsontools.dumps(payload), headers=headers)
            f = urllib2.urlopen(req)
            response = f.read()
            f.close()

            logger.info("pelisalacarta.platformcode.library get_data: response %s" %response)
            data = jsontools.loads(response)
        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("pelisalacarta.platformcode.library get_data: error en xbmc_json_rpc_url: %s" %message)
            data = ["error"]
    else:
        try:
            data = jsontools.loads(xbmc.executeJSONRPC(jsontools.dumps(payload)))
        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("pelisalacarta.platformcode.library get_data:: error en xbmc.executeJSONRPC: {0}".
                        format(message))
            data = ["error"]

    logger.info("pelisalacarta.platformcode.library get_data: data %s" %data)

    return data


def update(_path=''):
    """
    actualiza la libreria

    @type _path: str
    @param _path: ruta que hay que actualizar en la libreria
    """
    logger.info("pelisalacarta.platformcode.library update")
    # Se comenta la llamada normal para reutilizar 'payload' dependiendo del modo cliente
    #xbmc.executebuiltin('UpdateLibrary(video)')
    if _path:
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "params": {"directory": _path}, "id": 1}
    else:
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "id": 1}
    data = get_data(payload)
    logger.info("pelisalacarta.platformcode.library update data: %s" %data)


def clean(mostrar_dialogo=False):
    """
    limpia la libreria de elementos que no existen
    @param mostrar_dialogo: muestra el cuadro de progreso mientras se limpia la biblioteca
    @type mostrar_dialogo: bool
    """
    logger.info("pelisalacarta.platformcode.library clean")
    payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Clean", "id": 1,
               "params": {"showdialogs": mostrar_dialogo}}
    data = get_data(payload)
    logger.info("pelisalacarta.platformcode.library clean data: %s" %data)


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

    # Obtiene el listado de episodios
    itemlist = getattr(channel, item.action)(item)

    if not itemlist:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido a la biblioteca",
                                "No se ha podido obtener ningun episodio")
        logger.error("La serie %s no se ha podido añadir a la biblioteca. No se ha podido obtener ningun episodio"
                     %item.show)
        return

    insertados, sobreescritos, fallidos = save_library_tvshow(item, itemlist)

    if fallidos == -1:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido a la biblioteca")
        logger.error("La serie %s no se ha podido añadir a la biblioteca" %item.show)

    elif fallidos > 0:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido completa a la biblioteca")
        logger.error("No se han podido añadir %s episodios de la serie %s a la biblioteca" %(fallidos, item.show))
    else:
        platformtools.dialog_ok("Biblioteca", "La serie se ha añadido a la biblioteca")
        logger.info("[launcher.py] Se han añadido %s episodios de la serie %s a la biblioteca" %(insertados, item.show))


# metodos de menu contextual
def mark_content_as_watched(item, value=1):
    logger.info("pelisalacarta.platformcode.library mark_content_as_watched")
    #logger.debug("item:\n" + item.tostring('\n'))

    if filetools.exists(item.nfo):
        url_scraper = filetools.read(item.nfo, 0, 1)
        it = Item().fromjson(filetools.read(item.nfo, 1))

        if item.contentType == 'movie':
            name_file = os.path.splitext(os.path.basename(item.nfo))[0]
        else: #(item.contentType =='episode')
            name_file = item.contentTitle

        if not hasattr(it, 'library_playcounts'): it.library_playcounts = {}
        it.library_playcounts.update({name_file: value})

        # Guardamos los cambios en item.nfo
        if filetools.write(item.nfo, url_scraper + it.tojson()):
            item.infoLabels['playcount'] = value
            # Actualizamos la BBDD de Kodi
            mark_content_as_watched_on_kodi(item, value)

            import xbmc
            xbmc.executebuiltin("Container.Refresh")


def mark_season_as_watched(item, value=1):
    logger.info("pelisalacarta.platformcode.library mark_season_as_watched")
    '''mark_season_as_watched_on_kodi(item.contentSeason, value)
    raise'''
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
                it.library_playcounts[name_file] = value
                episodios_marcados += 1


    if episodios_marcados:
        # Añadimos la temporada al diccionario item.library_playcounts
        it.library_playcounts["season %s" %item.contentSeason] = value

        # Guardamos los cambios en tvshow.nfo
        filetools.write(f, url_scraper + it.tojson())
        item.infoLabels['playcount'] = value
        # Actualizamos la BBDD de Kodi
        mark_season_as_watched_on_kodi(item, value)

    import xbmc
    xbmc.executebuiltin("Container.Refresh")


def mark_tvshow_as_updatable(item, value=True):
    logger.info("pelisalacarta.platformcode.library mark_tvshow_as_updatable")
    url_scraper = filetools.read(item.nfo, 0, 1)
    it = Item().fromjson(filetools.read(item.nfo, 1))
    it.active = value
    filetools.write(item.nfo, url_scraper + it.tojson())

    item.active = value
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
