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
import sys
import urllib2
import xbmc
from threading import Thread
from core import config
from core import filetools
from core import jsontools
from core import logger
from core import scrapertools
from core import tmdb
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
xbmc_json_rpc_url = "http://" + xbmc_host + ":" + str(xbmc_port) + "/jsonrpc"


LIBRARY_PATH = config.get_library_path()
if not filetools.exists(LIBRARY_PATH):
    logger.info("pelisalacarta.platformcode.library Library path doesn't exist:" + LIBRARY_PATH)
    config.verify_directories_created()

# TODO permitir cambiar las rutas y nombres en settings para 'cine' y 'series'
FOLDER_MOVIES = "CINE"  # config.get_localized_string(30072)
MOVIES_PATH = filetools.join(LIBRARY_PATH, FOLDER_MOVIES)
FOLDER_TVSHOWS = "SERIES"  # config.get_localized_string(30073)
TVSHOWS_PATH = filetools.join(LIBRARY_PATH, FOLDER_TVSHOWS)


def read_nfo(path_nfo, item=None):
    """
    Metodo para leer archivos nfo.
        Los arcivos nfo tienen la siguiente extructura: url_scraper | xml + item_json
        [url_scraper] y [xml] son opcionales, pero solo uno de ellos ha de existir siempre.
    @param path_nfo: ruta absoluta al archivo nfo
    @type path_nfo: str
    @param item: Si se pasa este parametro el item devuelto sera una copia de este con
        los valores de 'infoLabels', 'library_playcounts' y 'path' leidos del nfo
    @type: Item
    @return: Una tupla formada por la 'url_scraper' y el objeto 'item_json'
    @rtype: tuple (str, Item)
    """
    url_scraper = ""
    it = None
    if filetools.exists(path_nfo):
        url_scraper = filetools.read(path_nfo, 0, 1)
        data = filetools.read(path_nfo, 1)

        if not url_scraper.startswith('http'):
            # url_scraper no valida, xml presente
            url_scraper = ''
            import re
            data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
            data = re.sub("(<tvshow>|<movie>)(.*?)(</tvshow>|</movie>)", "", data)

        it_nfo = Item().fromjson(data)


        if item:
            it = item.clone()
            it.infoLabels = it_nfo.infoLabels
            if 'library_playcounts' in it_nfo:
                it.library_playcounts = it_nfo.library_playcounts
            if it_nfo.path:
                it.path = it_nfo.path
        else:
            it = it_nfo

        if 'fanart' in it.infoLabels:
            it.fanart = it.infoLabels['fanart']

    return url_scraper, it


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
        logger.debug("NO ENCONTRADO contentTitle")
        return 0, 0, -1  # Salimos sin guardar

    # TODO configurar para segun el scraper se llamara a uno u otro
    tmdb_return = tmdb.find_and_set_infoLabels_tmdb(item)

    # Llegados a este punto podemos tener:
    #  tmdb_return = True: Un item con infoLabels con la información actualizada de la peli
    #  tmdb_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    #  item.infoLabels['imdb_id'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not tmdb_return or not item.infoLabels['imdb_id']:
        # TODO de momento si no hay resultado no añadimos nada,
        # aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        logger.debug("NO ENCONTRADO EN TMDB O NO TIENE IMDB_ID")
        return 0, 0, -1

    _id = item.infoLabels['imdb_id']

    # progress dialog
    p_dialog = platformtools.dialog_progress('pelisalacarta', 'Añadiendo película...')

    base_name = filetools.text2filename(item.contentTitle)

    for raiz, subcarpetas, ficheros in filetools.walk(MOVIES_PATH):
        for c in subcarpetas:
            if c.endswith("[%s]" % _id):
                path = filetools.join(raiz, c)
                break

    if not path:
        # Crear carpeta
        path = filetools.join(MOVIES_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.info("pelisalacarta.platformcode.library save_library_movie Creando directorio pelicula:" + path)
        try:
            filetools.mkdir(path)
        except OSError, exception:
            if exception.errno != errno.EEXIST:
                raise

    nfo_path = filetools.join(path, "%s [%s].nfo" % (base_name, _id))
    if not filetools.exists(nfo_path):
        # Creamos .nfo si no existe
        logger.info("Creando .nfo: " + nfo_path)
        url_scraper = "https://www.themoviedb.org/movie/%s\n" % item.infoLabels['tmdb_id']
        item_nfo = Item(title=item.contentTitle, channel="biblioteca", action='findvideos',
                    library_playcounts={"%s [%s]" % (base_name, _id): 0}, infoLabels=item.infoLabels,
                    library_urls={})

    else:
        # Si existe .nfo, pero estamos añadiendo un nuevo canal lo abrimos
        from channels import biblioteca
        '''url_scraper = filetools.read(nfo_path, 0, 1)
        item_nfo = Item().fromjson(filetools.read(nfo_path, 1))'''
        url_scraper, item_nfo = read_nfo(nfo_path)

    strm_path = filetools.join(path, "%s.strm" % base_name)
    if not filetools.exists(strm_path):
        # Crear base_name.strm si no existe
        item_strm = item.clone(channel='biblioteca', action='play_from_library',
                               strm_path=strm_path.replace(MOVIES_PATH, ""), contentType='movie',
                               infoLabels={'title': item.contentTitle})
        filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))
        item_nfo.strm_path = strm_path.replace(MOVIES_PATH, "")

    # Solo si existen item_nfo y .strm continuamos
    if item_nfo and filetools.exists(strm_path):
        json_path = filetools.join(path, ("%s [%s].json" % (base_name, item.channel)).lower())
        if filetools.exists(json_path):
            logger.info("pelisalacarta.platformcode.library savelibrary el fichero existe. Se sobreescribe")
            sobreescritos += 1
        else:
            insertados += 1

        if filetools.write(json_path, item.tojson()):
            p_dialog.update(100, 'Añadiendo película...', item.contentTitle)
            item_nfo.library_urls[item.channel] = item.url

            if filetools.write(nfo_path, url_scraper + item_nfo.tojson()):
                # actualizamos la biblioteca de Kodi con la pelicula
                if config.is_xbmc():
                    update(FOLDER_MOVIES, filetools.basename(path) + "/")

                p_dialog.close()
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
    path = ""

    # Si llegados a este punto no tenemos titulo o tmdb_id, salimos
    if not (item.contentSerieName or item.infoLabels['tmdb_id']) or not item.channel:
        logger.debug("NO ENCONTRADO contentSerieName NI tmdb_id")
        return 0, 0, -1  # Salimos sin guardar

    # TODO configurar para segun el scraper se llame a uno u otro
    tmdb_return = tmdb.find_and_set_infoLabels_tmdb(item)

    # Llegados a este punto podemos tener:
    #  tmdb_return = True: Un item con infoLabels con la información actualizada de la serie
    #  tmdb_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    #  item.infoLabels['imdb_id'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not tmdb_return or not item.infoLabels['imdb_id']:
        # TODO de momento si no hay resultado no añadimos nada,
        # aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        logger.debug("NO ENCONTRADO EN TMDB O NO TIENE IMDB_ID")
        return 0, 0, -1

    _id = item.infoLabels['imdb_id']
    if item.infoLabels['title']:
        base_name = item.infoLabels['title']
    else:
        base_name = item.contentSerieName

    base_name = filetools.text2filename(base_name)

    for raiz, subcarpetas, ficheros in filetools.walk(TVSHOWS_PATH):
        for c in subcarpetas:
            if c.endswith("[%s]" % _id):
                path = filetools.join(raiz, c)
                break

    if not path:
        path = filetools.join(TVSHOWS_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.info("Creando directorio serie: " + path)
        try:
            filetools.mkdir(path)
        except OSError, exception:
            if exception.errno != errno.EEXIST:
                raise

    # Eliminamos de la lista lo que no sean episodios
    for it in episodelist:
        if not scrapertools.get_season_and_episode(it.title):
            episodelist.remove(it)

    tvshow_path = filetools.join(path, "tvshow.nfo")
    if not filetools.exists(tvshow_path):
        # Creamos tvshow.nfo, si no existe, con la url_scraper, info de la serie y marcas de episodios vistos
        logger.info("Creando tvshow.nfo: " + tvshow_path)
        #url_scraper = "https://www.themoviedb.org/tv/%s\n" % item.infoLabels['tmdb_id']
        url_scraper = item.infoLabels['url_scraper'] + "\n"
        item_tvshow = Item(title=item.contentTitle, channel="biblioteca", action="get_temporadas",
                           fanart=item.infoLabels['fanart'], thumbnail=item.infoLabels['thumbnail'],
                           infoLabels=item.infoLabels, path=path.replace(TVSHOWS_PATH, ""))
        item_tvshow.library_playcounts = {}
        item_tvshow.library_urls = {item.channel: item.url}

    else:
        # Si existe tvshow.nfo, pero estamos añadiendo un nuevo canal actualizamos el listado de urls
        url_scraper, item_tvshow = read_nfo(tvshow_path)

        item_tvshow.library_urls[item.channel] = item.url

    # FILTERTOOLS
    # si el canal tiene filtro de idiomas, añadimos el canal y el show
    if episodelist and "list_idiomas" in episodelist[0]:
        # si ya hemos añadido un canal previamente con filtro, añadimos o actualizamos el canal y show
        if "library_filter_show" in item_tvshow:
            item_tvshow.library_filter_show[item.channel] = item.show
        # no habia ningún canal con filtro y lo generamos por primera vez
        else:
            item_tvshow.library_filter_show = {item.channel: item.show}


    if item.channel != "descargas":
        item_tvshow.active = 1  # para que se actualice a diario cuando se llame a library_service

    filetools.write(tvshow_path, url_scraper + item_tvshow.tojson())

    if not episodelist:
        # La lista de episodios esta vacia
        return 0, 0, 0

    # Guardar los episodios
    insertados, sobreescritos, fallidos = save_library_episodes(path, episodelist, item)

    # TODO si fallidos == -1 podriamos comprobar si es necesario eliminar la serie

    return insertados, sobreescritos, fallidos


def save_library_episodes(path, episodelist, serie, silent=False, overwrite=True):
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
    @param overwrite: permite sobreescribir los ficheros existentes
    @type overwrite: bool
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
    news_in_playcounts = {}

    # Silent es para no mostrar progreso (para library_service)
    if not silent:
        # progress dialog
        p_dialog = platformtools.dialog_progress('pelisalacarta', 'Añadiendo episodios...')
        p_dialog.update(0, 'Añadiendo episodio...')

    # fix float porque la division se hace mal en python 2.x
    t = float(100) / len(episodelist)

    for i, e in enumerate(episodelist):
        if not silent:
            p_dialog.update(int(math.ceil((i + 1) * t)), 'Añadiendo episodio...', e.title)

        try:
            season_episode = scrapertools.get_season_and_episode(e.title.lower())

            e.infoLabels = serie.infoLabels
            e.contentSeason, e.contentEpisodeNumber = season_episode.split("x")
            season_episode = "%sx%s" % (e.contentSeason, str(e.contentEpisodeNumber).zfill(2))
        except:
            continue

        strm_path = filetools.join(path, "%s.strm" % season_episode)
        if not filetools.exists(strm_path):
            # Si no existe season_episode.strm añadirlo
            item_strm = e.clone(action='play_from_library', channel='biblioteca',
                                strm_path=strm_path.replace(TVSHOWS_PATH, ""), infoLabels={})
            item_strm.contentSeason = e.contentSeason
            item_strm.contentEpisodeNumber = e.contentEpisodeNumber
            item_strm.contentType = e.contentType
            item_strm.contentTitle = season_episode

            # FILTERTOOLS
            # si el canal tiene filtro se le pasa el nombre que tiene guardado para que filtre correctamente,
            if item_strm.list_idiomas:
                # si viene de library_service se obtiene del fichero tvshow.nfo, propiedad "library_filter_show"
                if "library_filter_show" in serie:
                    item_strm.library_filter_show = serie.library_filter_show.get(serie.channel, "")
                # si se ha agregado la serie lo obtenemos del titulo.
                else:
                    item_strm.library_filter_show = {serie.channel: serie.show}

                if item_strm.library_filter_show == "":
                    logger.error("Se ha producido un error al obtener el nombre de la serie a filtrar")

            # logger.debug("item_strm" + item_strm.tostring('\n'))
            # logger.debug("serie " + serie.tostring('\n'))
            filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))

        nfo_path = filetools.join(path, "%s.nfo" % season_episode)
        item_nfo = None
        if not filetools.exists(nfo_path) and e.infoLabels.get("imdb_id"):
            # Si no existe season_episode.nfo añadirlo
            if e.infoLabels["tmdb_id"]:
                tmdb.find_and_set_infoLabels_tmdb(e)
                url_scraper = "https://www.themoviedb.org/tv/%s/season/%s/episode/%s\n" % (
                e.infoLabels['tmdb_id'],
                e.contentSeason,
                e.contentEpisodeNumber)


            elif e.infoLabels["tvdb_id"]:
                url_scraper = e.url_scraper

            item_nfo = e.clone(channel="biblioteca", url="", action='findvideos',
                               strm_path=strm_path.replace(TVSHOWS_PATH, ""))

            filetools.write(nfo_path, url_scraper + item_nfo.tojson())

        # Solo si existen season_episode.nfo y season_episode.strm continuamos
        json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())
        if filetools.exists(nfo_path) and filetools.exists(strm_path):
            nuevo = not filetools.exists(json_path)

            if nuevo or overwrite:
                # Obtenemos infoLabel del episodio
                if not item_nfo:
                    url_scraper, item_nfo = read_nfo(nfo_path)
                    #item_nfo = Item().fromjson(filetools.read(nfo_path, 1))

                e.infoLabels = item_nfo.infoLabels

                if filetools.write(json_path, e.tojson()):
                    if nuevo:
                        logger.info("pelisalacarta.platformcode.library savelibrary Insertado: %s" % json_path)
                        insertados += 1
                        # Marcamos episodio como no visto
                        news_in_playcounts[season_episode] = 0
                        # Marcamos la temporada como no vista
                        news_in_playcounts["season %s" % e.contentSeason] = 0
                        # Marcamos la serie como no vista
                        # logger.debug("serie " + serie.tostring('\n'))
                        news_in_playcounts[serie.contentTitle] = 0
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
            import datetime
            url_scraper, tvshow_item = read_nfo(tvshow_path)
            tvshow_item.library_playcounts.update(news_in_playcounts)

            if tvshow_item.active == 30:
                tvshow_item.active = 1
            next_update = datetime.date.today() + datetime.timedelta(days=int(tvshow_item.active))
            tvshow_item.next_update = next_update.strftime('%Y-%m-%d')

            filetools.write(tvshow_path, url_scraper + tvshow_item.tojson())
        except:
            logger.error("Error al actualizar tvshow.nfo")
            fallidos = -1

        # ... y actualizamos la biblioteca de Kodi
        if config.is_xbmc():
            update(FOLDER_TVSHOWS, filetools.basename(path) + "/")

    if fallidos == len(episodelist):
        fallidos = -1

    logger.debug("%s [%s]: insertados= %s, sobreescritos= %s, fallidos= %s" %
                 (serie.contentSerieName, serie.channel, insertados, sobreescritos, fallidos))
    return insertados, sobreescritos, fallidos


def add_pelicula_to_library(item):
    """
        guarda una pelicula en la libreria de cine. La pelicula puede ser un enlace dentro de un canal o un video
        descargado previamente.

        Para añadir episodios descargados en local, el item debe tener exclusivamente:
            - contentTitle: titulo de la pelicula
            - title: titulo a mostrar junto al listado de enlaces -findvideos- ("Reproducir video local HD")
            - infoLabels["tmdb_id"] o infoLabels["imdb_id"]
            - contentType == "movie"
            - channel = "descargas"
            - url : ruta local al video

        @type item: item
        @param item: elemento que se va a guardar.
    """
    logger.info("pelisalacarta.platformcode.library add_pelicula_to_library")

    new_item = item.clone(action="findvideos")
    insertados, sobreescritos, fallidos = save_library_movie(new_item)

    if fallidos == 0:
        platformtools.dialog_ok(config.get_localized_string(30131), new_item.contentTitle,
                                config.get_localized_string(30135))  # 'se ha añadido a la biblioteca'
    else:
        platformtools.dialog_ok(config.get_localized_string(30131),
                                "ERROR, la pelicula NO se ha añadido a la biblioteca")


def add_serie_to_library(item, channel=None):
    """
        Guarda contenido en la libreria de series. Este contenido puede ser uno de estos dos:
            - La serie con todos los capitulos incluidos en la lista episodelist.
            - Un solo capitulo descargado previamente en local.

        Para añadir episodios descargados en local, el item debe tener exclusivamente:
            - contentSerieName (o show): Titulo de la serie
            - contentTitle: titulo del episodio para extraer season_and_episode ("1x01 Piloto")
            - title: titulo a mostrar junto al listado de enlaces -findvideos- ("Reproducir video local")
            - infoLabels["tmdb_id"] o infoLabels["imdb_id"]
            - contentType != "movie"
            - channel = "descargas"
            - url : ruta local al video

        @type item: item
        @param item: item que representa la serie a guardar
        @type channel: modulo
        @param channel: canal desde el que se guardara la serie.
            Por defecto se importara item.from_channel o item.channel

    """
    logger.info("pelisalacarta.platformcode.library add_serie_to_library, show=#" + item.show + "#")
    # logger.debug(item.tostring('\n'))

    if item.channel == "descargas":
        itemlist = [item.clone()]

    else:
        # Esta marca es porque el item tiene algo más aparte en el atributo "extra"
        item.action = item.extra
        if "###" in item.extra:
            item.action = item.extra.split("###")[0]
            item.extra = item.extra.split("###")[1]

        if item.from_action:
            item.__dict__["action"] = item.__dict__.pop("from_action")
        if item.from_channel:
            item.__dict__["channel"] = item.__dict__.pop("from_channel")

        if not channel:
            try:
                channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
            except ImportError:
                exec "import channels." + item.channel + " as channel"

        # Obtiene el listado de episodios
        itemlist = getattr(channel, item.action)(item)

    # Eliminamos de la lista lo q no sean episodios
    for it in itemlist:
        if not scrapertools.get_season_and_episode(it.title):
            itemlist.remove(it)


    if not itemlist:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido a la biblioteca",
                                "No se ha podido obtener ningun episodio")
        logger.error("La serie %s no se ha podido añadir a la biblioteca. No se ha podido obtener ningun episodio"
                     % item.show)
        return

    insertados, sobreescritos, fallidos = save_library_tvshow(item, itemlist)

    if fallidos == -1:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido a la biblioteca")
        logger.error("La serie %s no se ha podido añadir a la biblioteca" % item.show)

    elif fallidos > 0:
        platformtools.dialog_ok("Biblioteca", "ERROR, la serie NO se ha añadido completa a la biblioteca")
        logger.error("No se han podido añadir %s episodios de la serie %s a la biblioteca" % (fallidos, item.show))
    else:
        platformtools.dialog_ok("Biblioteca", "La serie se ha añadido a la biblioteca")
        logger.info("[launcher.py] Se han añadido %s episodios de la serie %s a la biblioteca" %
                    (insertados, item.show))


'''
Codigo exclusivo para kodi/xbmc
'''


def mark_auto_as_watched(item):
    def mark_as_watched_subThread(item):
        logger.info("pelisalacarta.platformcode.library mark_as_watched_subThread")
        # logger.debug("item:\n" + item.tostring('\n'))

        condicion = int(config.get_setting("watched_setting"))

        xbmc.sleep(5000)

        while xbmc.Player().isPlaying():
            tiempo_actual = xbmc.Player().getTime()
            totaltime = xbmc.Player().getTotalTime()

            mark_time = 0
            if condicion == 0:  # '5 minutos'
                mark_time = 300000  # FOR DEBUG = 30
            elif condicion == 1:  # '30%'
                mark_time = totaltime * 0.3
            elif condicion == 2:  # '50%'
                mark_time = totaltime * 0.5
            elif condicion == 3:  # '80%'
                mark_time = totaltime * 0.8

            # logger.debug(str(tiempo_actual))
            # logger.debug(str(mark_time))

            if tiempo_actual > mark_time:
                item.playcount = 1
                from channels import biblioteca
                biblioteca.mark_content_as_watched(item)
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
    # logger.debug("item:\n" + item.tostring('\n'))
    payload_f = ''

    if item.contentType == "movie":
        movieid = 0
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies",
                   "params": {"properties": ["title", "playcount", "originaltitle", "file"]},
                   "id": 1}

        data = get_data(payload)
        if 'result' in data:
            for d in data['result']['movies']:

                filename = filetools.basename(item.strm_path)
                head, tail = filetools.split(filetools.split(item.strm_path)[0])
                path = filetools.join(tail, filename)
                if d['file'].replace("/", "\\").endswith(path.replace("/", "\\")):
                    # logger.debug("marco la pelicula como vista")
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

                filename = filetools.basename(item.strm_path)
                head, tail = filetools.split(filetools.split(item.strm_path)[0])
                path = filetools.join(tail, filename)
                if d['file'].replace("/", "\\").endswith(path.replace("/", "\\")):
                    # logger.debug("marco el episodio como visto")
                    episodeid = d['episodeid']
                    break

        if episodeid != 0:
            payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {
                "episodeid": episodeid, "playcount": value}, "id": 1}

    if payload_f:
        # Marcar como visto
        data = get_data(payload_f)
        # logger.debug(str(data))
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
    logger.info("pelisalacarta.platformcode.library mark_season_as_watched_on_kodi")
    # logger.debug("item:\n" + item.tostring('\n'))

    # Solo podemos marcar la temporada como vista en la BBDD de Kodi si la BBDD es local,
    # en caso de compartir BBDD esta funcionalidad no funcionara
    if modo_cliente:
        return

    if value == 0:
        value = 'Null'

    request_season = ''
    if item.contentSeason > -1:
        request_season = ' and c12= %s' % item.contentSeason

    item_path1 = "%" + item.path.replace("\\\\", "\\").replace(TVSHOWS_PATH, "")
    if item_path1[:-1] != "\\":
        item_path1 += "\\"
    item_path2 = item_path1.replace("\\", "/")

    sql = 'update files set playCount= %s where idFile  in ' \
          '(select idfile from episode_view where strPath like "%s" or strPath like "%s"%s)' % \
          (value, item_path1, item_path2, request_season)

    execute_sql_kodi(sql)


def execute_sql_kodi(sql):
    """
    Ejecuta la consulta sql contra la base de datos de kodi
    @param sql: Consulta sql valida
    @type sql: str
    @return: Numero de registros modificados o devueltos por la consulta
    @rtype nun_records: int
    @return: lista con el resultado de la consulta
    @rtype records: list of tuples
    """
    logger.info("pelisalacarta.platformcode.library execute_sql_kodi")
    file_db = ""
    nun_records = 0
    records = None

    # Buscamos el nombre de la BBDD de videos segun la version de kodi
    code_db = {'10': 'MyVideos37.db', '11': 'MyVideos60.db', '12': 'MyVideos75.db', '13': 'MyVideos78.db',
               '14': 'MyVideos90.db', '15': 'MyVideos93.db', '16': 'MyVideos99.db', '17': 'MyVideos107.db'}

    video_db = code_db.get(xbmc.getInfoLabel("System.BuildVersion").split(".", 1)[0], '')
    if video_db:
        file_db = filetools.join(xbmc.translatePath("special://userdata/Database"), video_db)

    # metodo alternativo para localizar la BBDD
    if not file_db or not filetools.exists(file_db):
        file_db = ""
        for f in filetools.listdir(xbmc.translatePath("special://userdata/Database")):
            path_f = filetools.join(xbmc.translatePath("special://userdata/Database"), f)

            if filetools.isfile(path_f) and f.lower().startswith('myvideos') and f.lower().endswith('.db'):
                file_db = path_f
                break

    if file_db:
        logger.info("Archivo de BD: %s" % file_db)
        conn = None
        try:
            import sqlite3
            conn = sqlite3.connect(file_db)
            cursor = conn.cursor()

            logger.info("Ejecutando sql: %s" % sql)
            cursor.execute(sql)
            conn.commit()

            records = cursor.fetchall()
            if sql.lower().startswith("select"):
                nun_records = len(records)
                if nun_records == 1 and records[0][0] is None:
                    nun_records = 0
                    records = []
            else:
                nun_records = conn.total_changes

            conn.close()
            logger.info("Consulta ejecutada. Registros: %s" % nun_records)

        except:
            logger.error("Error al ejecutar la consulta sql")
            if conn:
                conn.close()

    else:
        logger.debug("Base de datos no encontrada")

    return nun_records, records


def get_data(payload):
    """
    obtiene la información de la llamada JSON-RPC con la información pasada en payload
    @type payload: dict
    @param payload: data
    :return:
    """
    logger.info("pelisalacarta.platformcode.library get_data: payload %s" % payload)
    # Required header for XBMC JSON-RPC calls, otherwise you'll get a 415 HTTP response code - Unsupported media type
    headers = {'content-type': 'application/json'}

    if modo_cliente:
        try:
            req = urllib2.Request(xbmc_json_rpc_url, data=jsontools.dump_json(payload), headers=headers)
            f = urllib2.urlopen(req)
            response = f.read()
            f.close()

            logger.info("pelisalacarta.platformcode.library get_data: response %s" % response)
            data = jsontools.load_json(response)
        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("pelisalacarta.platformcode.library get_data: error en xbmc_json_rpc_url: %s" % message)
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

    logger.info("pelisalacarta.platformcode.library get_data: data %s" % data)

    return data


def update(content_type=FOLDER_TVSHOWS, folder=""):
    """
    Actualiza la libreria dependiendo del tipo de contenido y la ruta que se le pase.

    @type content_type: str
    @param content_type: tipo de contenido para actualizar, series o peliculas
    @type folder: str
    @param folder: nombre de la carpeta a escanear.
    """
    logger.info("pelisalacarta.platformcode.library update")

    librarypath = config.get_setting("librarypath")
    if librarypath == "":
        librarypath = "special://home/userdata/addon_data/plugin.video." + config.PLUGIN_NAME + "/library/" + \
                      content_type + "/"
    else:
        if folder == "":
            librarypath = ""
        else:
            librarypath = filetools.join(librarypath, content_type, folder)

    # logger.info("la ruta es " + librarypath)
    _path = librarypath

    # Se comenta la llamada normal para reutilizar 'payload' dependiendo del modo cliente
    # xbmc.executebuiltin('UpdateLibrary(video)')
    if _path:
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "params": {"directory": _path}, "id": 1}
    else:
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "id": 1}
    data = get_data(payload)
    logger.info("pelisalacarta.platformcode.library update data: %s" % data)


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
    logger.info("pelisalacarta.platformcode.library clean data: %s" % data)


def establecer_contenido(content_type, silent=False):
    if config.is_xbmc():
        continuar = False

        librarypath = config.get_setting("librarypath")
        if librarypath == "":
            continuar = True
            if content_type == FOLDER_MOVIES:
                if not xbmc.getCondVisibility('System.HasAddon(metadata.themoviedb.org)'):
                    if not silent:
                        # Preguntar si queremos instalar metadata.themoviedb.org
                        install = platformtools.dialog_yesno("The Movie Database",
                                                             "No se ha encontrado el Scraper de películas de TheMovieDB.",
                                                             "¿Desea instalarlo ahora?")
                    else:
                        install = True

                    if install:
                        try:
                            # Instalar metadata.themoviedb.org
                            xbmc.executebuiltin('xbmc.installaddon(metadata.themoviedb.org)', True)
                            logger.info("Instalado el Scraper de películas de TheMovieDB")
                        except:
                            pass

                    continuar = (install and xbmc.getCondVisibility('System.HasAddon(metadata.themoviedb.org)'))

            else: # SERIES
                # Instalar The TVDB
                if not xbmc.getCondVisibility('System.HasAddon(metadata.tvdb.com)'):
                    if not silent:
                        # Preguntar si queremos instalar metadata.tvdb.com
                        install = platformtools.dialog_yesno("The TVDB",
                                                             "No se ha encontrado el Scraper de series de The TVDB.",
                                                             "¿Desea instalarlo ahora?")
                    else:
                        install = True

                    if install:
                        try:
                            # Instalar metadata.tvdb.com
                            xbmc.executebuiltin('xbmc.installaddon(metadata.tvdb.com)', True)
                            logger.info("Instalado el Scraper de series de The TVDB")
                        except:
                            pass

                    continuar = (install and xbmc.getCondVisibility('System.HasAddon(metadata.tvdb.com)'))


                # Instalar TheMovieDB
                if continuar and not xbmc.getCondVisibility('System.HasAddon(metadata.tvshows.themoviedb.org)'):
                    if not silent:
                        # Preguntar si queremos instalar metadata.tvshows.themoviedb.org
                        install = platformtools.dialog_yesno("The Movie Database",
                                                             "No se ha encontrado el Scraper de series de TheMovieDB.",
                                                             "¿Desea instalarlo ahora?")
                    else:
                        install = True

                    if install:
                        try:
                            # Instalar metadata.tvshows.themoviedb.org
                            xbmc.executebuiltin('xbmc.installaddon(metadata.tvshows.themoviedb.org)', True)
                            strSettings = '<settings>\n\t<setting id="fanart" value="true" />\n\t' \
                                          '<setting id="keeporiginaltitle" value="false" />\n\t' \
                                          '<setting id="language" value="es" />\n' \
                                          '</settings>'
                            path_settings = xbmc.translatePath("special://profile/addon_data/metadata.tvshows.themoviedb.org/settings.xml")
                            install = filetools.write(path_settings,strSettings)
                            logger.info("Instalado el Scraper de series de TheMovieDB")
                        except:
                            pass

                    continuar = (install and xbmc.getCondVisibility('System.HasAddon(metadata.tvshows.themoviedb.org)'))

            idPath = 0
            idParentPath = 0
            strPath = ""
            if continuar:
                continuar = False
                librarypath = "special://home/userdata/addon_data/plugin.video." + config.PLUGIN_NAME + "/library/"

                # Buscamos el idPath
                sql = 'SELECT MAX(idPath) FROM path'
                nun_records, records = execute_sql_kodi(sql)
                if nun_records == 1:
                    idPath = records[0][0] + 1


                # Buscamos el idParentPath
                sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % \
                                            librarypath.replace('/profile/', '/%/').replace('/home/userdata/', '/%/')
                nun_records, records = execute_sql_kodi(sql)
                if nun_records == 1:
                    idParentPath = records[0][0]
                    librarypath = records[0][1]
                    continuar = True
                else:
                    # No existe librarypath en la BD: la insertamos
                    sql = 'INSERT INTO path (idPath, strPath,  scanRecursive, useFolderNames, noUpdate, exclude) VALUES ' \
                          '(%s, "%s", 0, 0, 0, 0)' % (idPath, librarypath)
                    nun_records, records = execute_sql_kodi(sql)
                    if nun_records == 1:
                        continuar = True
                        idParentPath = idPath
                        idPath += 1

            if continuar:
                continuar = False

                # Fijamos strContent, strScraper, scanRecursive y strSettings
                if content_type == FOLDER_MOVIES:
                    strContent = 'movies'
                    strScraper = 'metadata.themoviedb.org'
                    scanRecursive = 2147483647
                    strSettings = "<settings><setting id='RatingS' value='TMDb' /><setting id='certprefix' value='Rated ' />" \
                                  "<setting id='fanart' value='true' /><setting id='keeporiginaltitle' value='false' />" \
                                  "<setting id='language' value='es' /><setting id='tmdbcertcountry' value='us' />" \
                                  "<setting id='trailer' value='true' /></settings>"
                    strActualizar = "¿Desea configurar este Scraper en español como opción por defecto para películas?"

                else:
                    strContent = 'tvshows'
                    strScraper = 'metadata.tvdb.com'
                    scanRecursive = 0
                    strSettings = "<settings><setting id='RatingS' value='TheTVDB' />" \
                                  "<setting id='absolutenumber' value='false' />" \
                                  "<setting id='dvdorder' value='false' />" \
                                  "<setting id='fallback' value='true' />" \
                                  "<setting id='fanart' value='true' />" \
                                  "<setting id='language' value='es' /></settings>"
                    strActualizar = "¿Desea configurar este Scraper en español como opción por defecto para series?"

                # Fijamos strPath
                strPath = librarypath + content_type + "/"
                logger.info("%s: %s" % (content_type, strPath))

                # Comprobamos si ya existe strPath en la BD para evitar duplicados
                sql = 'SELECT idPath FROM path where strPath="%s"' % strPath
                nun_records, records = execute_sql_kodi(sql)
                sql = ""
                if nun_records == 0:
                    # Insertamos el scraper
                    sql = 'INSERT INTO path (idPath, strPath, strContent, strScraper, scanRecursive, useFolderNames, ' \
                          'strSettings, noUpdate, exclude, idParentPath) VALUES (%s, "%s", "%s", "%s", %s, 0, ' \
                          '"%s", 0, 0, %s)' % (
                          idPath, strPath, strContent, strScraper, scanRecursive, strSettings, idParentPath)
                else:
                    if not silent:
                        # Preguntar si queremos configurar themoviedb.org como opcion por defecto
                        actualizar = platformtools.dialog_yesno("The TVDB", strActualizar)
                    else:
                        actualizar = True

                    if actualizar:
                        # Actualizamos el scraper
                        idPath = records[0][0]
                        sql = 'UPDATE path SET strContent="%s", strScraper="%s", scanRecursive=%s, strSettings="%s" ' \
                              'WHERE idPath=%s' % (strContent, strScraper, scanRecursive, strSettings, idPath)

                if sql:
                    nun_records, records = execute_sql_kodi(sql)
                    if nun_records == 1:
                        continuar = True
                        logger.info("Biblioteca  %s configurada" % content_type)

        if not continuar:
            heading = "Biblioteca no configurada"
            msg_text = "Asegurese de tener instalado el scraper de The Movie Database"
            platformtools.dialog_notification(heading, msg_text, icon=1, time=8000)
            logger.info("%s: %s" % (heading,msg_text))



'''
Main
'''
if not filetools.exists(MOVIES_PATH):
    logger.info("pelisalacarta.platformcode.library Movies path doesn't exist:" + MOVIES_PATH)
    if filetools.mkdir(MOVIES_PATH):
        establecer_contenido(FOLDER_MOVIES)


if not filetools.exists(TVSHOWS_PATH):
    logger.info("pelisalacarta.platformcode.library Tvshows path doesn't exist:" + TVSHOWS_PATH)
    if filetools.mkdir(TVSHOWS_PATH):
        establecer_contenido(FOLDER_TVSHOWS)