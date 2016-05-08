# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Herramientas de integración en Librería
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import errno
import os
import string
import sys
import urllib

import xbmc
from core import config
from core import jsontools
from core import logger
from core import scrapertools
from lib.samba import libsmb as samba

# TODO EVITAR USAR REQUESTS
from lib import requests

modo_cliente = int(config.get_setting("library_mode"))
# Host name where XBMC is running, leave as localhost if on this PC
# Make sure "Allow control of XBMC via HTTP" is set to ON in Settings ->
# Services -> Webserver
xbmc_host = config.get_setting("xbmc_host")
# Configured in Settings -> Services -> Webserver -> Port
xbmc_port = int(config.get_setting("xbmc_port"))
marcar_como_visto = bool(config.get_setting("mark_as_watched"))
# Base URL of the json RPC calls. For GET calls we append a "request" URI
# parameter. For POSTs, we add the payload as JSON the the HTTP request body
xbmc_json_rpc_url = "http://{host}:{port}/jsonrpc".format(host=xbmc_host, port=xbmc_port)

DEBUG = True


def path_exists(path):
    """
    comprueba si la ruta existe, samba necesita la raíz para conectar y la carpeta
    @type path: string
    @param path: la ruta del fichero
    @rtype:   string
    @return:  devuelve si existe la ruta.
    """
    if not samba.usingsamba(path):
        return os.path.exists(path)
    else:
        path_samba, folder_samba = path.rsplit('/', 1)
        return samba.folder_exists(folder_samba, path_samba)


def make_dir(path):
    """
    crea un directorio, samba necesita la raíz para conectar y la carpeta
    @type path: string
    @param path: la ruta del fichero
    """
    if not samba.usingsamba(path):
        os.mkdir(path)
    else:
        path_samba, folder_samba = path.rsplit('/', 1)
        samba.create_directory(folder_samba, path_samba)


def join_path(path, name):
    """
    une la ruta, el name puede ser carpeta o archivo
    @type path: string
    @param path: la ruta del fichero
    @type name: string
    @param name: nombre del fichero
    @rtype:   string
    @return:  devuelve si existe la ruta.
    """
    if not samba.usingsamba(path):
        path = xbmc.translatePath(os.path.join(path, name))
    else:
        path = path + "/" + name

    return path


LIBRARY_PATH = config.get_library_path()
if not samba.usingsamba(LIBRARY_PATH):
    if not path_exists(LIBRARY_PATH):
        logger.info("[library.py] Library path doesn't exist:"+LIBRARY_PATH)
        config.verify_directories_created()

# TODO permitir cambiar las rutas y nombres en settings para 'cine' y 'series'
FOLDER_MOVIES = "CINE"  # config.get_localized_string(30072)
MOVIES_PATH = join_path(LIBRARY_PATH, FOLDER_MOVIES)
if not path_exists(MOVIES_PATH):
    logger.info("[library.py] Movies path doesn't exist:"+MOVIES_PATH)
    make_dir(MOVIES_PATH)

FOLDER_TVSHOWS = "SERIES"  # config.get_localized_string(30073)
TVSHOWS_PATH = join_path(LIBRARY_PATH, FOLDER_TVSHOWS)
if not path_exists(TVSHOWS_PATH):
    logger.info("[library.py] Tvshows path doesn't exist:"+TVSHOWS_PATH)
    make_dir(TVSHOWS_PATH)

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
    logger.info("[library.py] is_compatible")
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
    logger.info("[library.py] library_in_kodi")
    # TODO arreglar
    return True

    path = xbmc.translatePath(os.path.join("special://masterprofile/", "sources.xml"))
    data = read_file(path)

    if config.get_library_path() in data:
        return True
    else:
        return False


def elimina_tildes(s):
    """
    elimina las tildes de la cadena
    @type s: string
    @param s: cadena.
    @rtype:   string
    @return:  cadena sin tildes.
    """
    logger.info("[library.py] elimina_tildes")
    import unicodedata
    if not isinstance(s, unicode):
        s = s.decode("UTF-8")
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def title_to_filename(title):
    """
    devuelve un titulo con caracteres válidos para crear un fichero
    @type title: string
    @param title: title.
    @rtype:   string
    @return:  cadena correcta sin tildes.
    """
    logger.info("[library.py] title_to_filename")
    safechars = string.letters + string.digits + " -_."
    folder_name = filter(lambda c: c in safechars, elimina_tildes(title))
    return str(folder_name)


def savelibrary(item):
    """
    guarda en la ruta correspondiente el elemento item, con los valores que contiene.
    @type item: item
    @param item: elemento que se va a guardar.
    @rtype:   int
    @return:  el número de elemento insertado.
    """
    logger.info("[library.py] savelibrary")

    path = LIBRARY_PATH
    filename = ""

    # MOVIES
    if item.category == "Cine":  # config.get_localized_string(30072):
        path = MOVIES_PATH
        filename = title_to_filename(item.fulltitle) + ".strm"
    # TVSHOWS
    elif item.category == "Series":  # config.get_localized_string(30073):

        if item.show == "":
            return -1  # Salimos sin guardar

        tvshow = title_to_filename(item.show)
        path = join_path(TVSHOWS_PATH, tvshow)

        if not path_exists(path):
            logger.info("[library.py] savelibrary Creando directorio serie:"+path)
            try:
                make_dir(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

        season_episode = scrapertools.get_season_and_episode(item.title.lower())
        logger.info("{title} -> {name}".format(title=item.title, name=season_episode))
        filename = "{name}.strm".format(name=season_episode)

    fullfilename = join_path(path, filename)

    addon_name = sys.argv[0]
    if addon_name.strip() == "":
        addon_name = "plugin://plugin.video.pelisalacarta/"

    save_file('{addon}?{url}'.format(addon=addon_name, url=item.tourl()), fullfilename)

    if path_exists(fullfilename):
        logger.info("[library.py] savelibrary el fichero existe. Se sobreescribe")
        nuevo = 0
    else:
        nuevo = 1

    logger.info("[library.py] savelibrary - Fin")

    return nuevo


def read_file(fname):
    """
    pythonic way to read from file

    @type  fname: string
    @param fname: filename.

    @rtype:   string
    @return:  data from filename.
    """
    logger.info("[library.py] read_file")
    data = ""

    if not samba.usingsamba(fname):
        if os.path.isfile(fname):
            try:
                with open(fname, "r") as f:
                    for line in f:
                        data += line
            except EnvironmentError:
                logger.info("ERROR al leer el archivo: {0}".format(fname))
    else:
        path, filename = fname.rsplit('/', 1)
        if samba.file_exists(filename, path):
            try:
                with samba.get_file_handle_for_reading(filename, path) as f:
                    for line in f:
                        data += line
            except EnvironmentError:
                logger.info("ERROR al leer el archivo: {0}".format(fname))

    # logger.info("[library.py] read_file-data {0}".format(data))
    return data


def save_file(data, fname):
    """
    pythonic way to write a file

    @type  fname: string
    @param fname: filename.
    @type  data: string
    @param data: data to save.

    @rtype:   bool
    @return:  result of saving.
    """
    logger.info("[library.py] save_file")
    logger.info("default encoding: {0}".format(sys.getdefaultencoding()))
    if not samba.usingsamba(fname):
        try:
            with open(fname, "w") as f:
                try:
                    f.write(data)
                except UnicodeEncodeError:
                    logger.info("Error al realizar el encode, se usa uft8")
                    f.write(data.encode('utf-8'))
        except EnvironmentError:
            logger.info("[library.py] save_file - Error al guardar el archivo: {0}".format(fname))
            return False
    else:
        try:
            path, filename = fname.rsplit('/', 1)
            samba.store_File(filename, data, path)
        except EnvironmentError:
            logger.info("[library.py] save_file - Error al guardar el archivo: {0}".format(fname))
            return False

    return True


def set_infoLabels_from_library(itemlist, tipo):
    """
    guarda los datos (thumbnail, fanart, plot, actores, etc) a mostrar de la library de Kodi.
    @type itemlist: list
    @param itemlist: item
    @type tipo: string
    @param tipo:
    @rtype:   infoLabels
    @return:  result of saving.
    """
    logger.info("[library.py] set_infoLabels_from_library")
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
    # logger.debug("JSON-RPC: {0}".format(data))

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
                if os.path.basename(i.path) == r_filename:
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


def clean_up_file(item):
    """
    borra los elementos del fichero "series" que no existen como carpetas en la libreria de "SERIES"
    @type item: item
    @param item: elemento
    @rtype:   list
    @return:  vacío para navegue.
    """
    logger.info("[library.py] clean_up_file")

    path = TVSHOWS_PATH

    dict_data = item.dict_fichero

    # Obtenemos las carpetas de las series
    raiz, carpetas_series, files = os.walk(path).next()

    for channel in dict_data.keys():
        for tvshow in dict_data[channel].keys():
            if tvshow not in carpetas_series:
                dict_data[channel].pop(tvshow, None)
                if not dict_data[channel]:
                    dict_data.pop(channel, None)

    json_data = jsontools.dump_json(dict_data)
    save_file(json_data, join_path(config.get_data_path(), TVSHOW_FILE))

    return []


def save_tvshow_in_file(item):
    """
    guarda nombre de la serie, canal y url para actualizar dentro del fichero 'series.xml'
    @type item: item
    @param item: elemento
    """
    logger.info("[library.py] save_tvshow_in_file")
    fname = os.path.join(config.get_data_path(), TVSHOW_FILE)
    # comprobación por si no ha llamada al library_service para ejecutar library.convert_xml_to_json()
    if not os.path.isfile(fname):
        convert_xml_to_json(True)

    dict_data = jsontools.load_json(read_file(fname))
    dict_data[item.channel][title_to_filename(item.show)] = item.url
    logger.info("dict_data {0}".format(dict_data))
    json_data = jsontools.dump_json(dict_data)
    save_file(json_data, fname)


def mark_as_watched(category, id_video=0):
    """
    marca el capitulo como visto en la libreria de Kodi
    @type category: string
    @param category: categoria "Series" o "Cine"
    @type id_video: int
    @param id_video: identificador 'episodeid' o 'movieid' en la BBDD
    """
    logger.info("[library.py] mark_as_watched - category:{0}".format(category))

    logger.info("se espera 5 segundos por si falla al reproducir el fichero")
    xbmc.sleep(5000)

    if not is_compatible() or not marcar_como_visto:
        return

    if xbmc.Player().isPlaying():
        payload = {"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}
        data = get_data(payload)

        if data['result']:
            payload_f = ''
            player_id = data['result'][0]["playerid"]

            if category == "Series":
                episodeid = id_video
                if episodeid == 0:
                    payload = {"jsonrpc": "2.0", "params": {"playerid": player_id,
                                                            "properties": ["season", "episode", "file", "showtitle"]},
                               "method": "Player.GetItem", "id": "libGetItem"}

                    data = get_data(payload)
                    if data['result']:
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
                        if data['result']:
                            for d in data['result']['episodes']:
                                if d['showtitle'] == showtitle:
                                    episodeid = d['episodeid']
                                    break

                if episodeid != 0:
                    payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {
                        "episodeid": episodeid, "playcount": 1}, "id": 1}

            else:  # Categoria == 'Movies'
                movieid = id_video
                if movieid == 0:

                    payload = {"jsonrpc": "2.0", "method": "Player.GetItem",
                               "params": {"playerid": 1,
                                          "properties": ["year", "file", "title", "uniqueid", "originaltitle"]},
                               "id": "libGetItem"}

                    data = get_data(payload)
                    if data['result']:
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
                        if data['result']:
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

                    if data['result']:
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
    logger.info("[library.py] get_data:: payload {0}".format(payload))
    # Required header for XBMC JSON-RPC calls, otherwise you'll get a 415 HTTP response code - Unsupported media type
    headers = {'content-type': 'application/json'}

    if modo_cliente:
        try:
            response = requests.post(xbmc_json_rpc_url, data=jsontools.dump_json(payload), headers=headers)
            logger.info("[library.py] get_data:: response {0}".format(response))
            data = jsontools.load_json(response.text)
        except requests.exceptions.ConnectionError:
            logger.info("[library.py] get_data:: xbmc_json_rpc_url: Error de conexion")
            data = ["error"]
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("[library.py] get_data:: error en xbmc_json_rpc_url: {0}".format(message))
            data = ["error"]
    else:
        try:
            data = jsontools.load_json(xbmc.executeJSONRPC(jsontools.dump_json(payload)))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info("[library.py] get_data:: error en xbmc.executeJSONRPC: {0}".format(message))
            data = ["error"]

    logger.info("[library.py] get_data:: data {0}".format(data))

    return data


def check_tvshow_xml():
    logger.info("[library.py] check_tvshow_xml")
    fname = os.path.join(config.get_data_path(), TVSHOW_FILE_OLD)
    flag = True
    if not os.path.exists(fname):
        flag = False
    else:
        data = read_file(fname)
        if data == "":
            flag = False

    convert_xml_to_json(flag)


def convert_xml_to_json(flag):
    logger.info("[library.py] convert_xml_to_json:: flag:{0}".format(flag))
    if flag:
        fname = os.path.join(config.get_data_path(), TVSHOW_FILE_OLD)

        dict_data = {}

        if os.path.isfile(fname):
            try:
                with open(fname, "r") as f:
                    for line in f:
                        aux = line.rstrip('\n').split(",")
                        tvshow = aux[0].strip()
                        url = aux[1].strip()
                        channel = aux[2].strip()

                        if channel in dict_data:
                            dict_data[channel][tvshow] = url
                        else:
                            dict_data.update({channel: {tvshow: url}})

            except EnvironmentError:
                logger.info("ERROR al leer el archivo: {0}".format(fname))
            else:
                os.rename(os.path.join(config.get_data_path(), TVSHOW_FILE_OLD),
                          os.path.join(config.get_data_path(), "series_old.xml"))

                json_data = jsontools.dump_json(dict_data)
                save_file(json_data, os.path.join(config.get_data_path(), TVSHOW_FILE))
