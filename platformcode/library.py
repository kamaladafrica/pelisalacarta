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

# TODO EVITAR USAR REQUESTS
from lib import requests

# Host name where XBMC is running, leave as localhost if on this PC
# Make sure "Allow control of XBMC via HTTP" is set to ON in Settings ->
# Services -> Webserver
xbmc_host = 'localhost'  # TODO meterlo en settings

# Configured in Settings -> Services -> Webserver -> Port
xbmc_port = 555  # TODO meterlo en settings

modo_cliente = False  # TODO sacarlo de settings config.get....

# Base URL of the json RPC calls. For GET calls we append a "request" URI
# parameter. For POSTs, we add the payload as JSON the the HTTP request body
xbmc_json_rpc_url = "http://{host}:{port}/jsonrpc".format(host=xbmc_host, port=xbmc_port)

DEBUG = True

LIBRARY_PATH = config.get_library_path()
if not os.path.exists(LIBRARY_PATH):
    logger.info("[library.py] Library path doesn't exist:"+LIBRARY_PATH)
    config.verify_directories_created()

# TODO permitir cambiar las rutas y nombres en settings para 'cine' y 'series'
FOLDER_MOVIES = "CINE"  # config.get_localized_string(30072)
MOVIES_PATH = xbmc.translatePath(os.path.join(LIBRARY_PATH, FOLDER_MOVIES))
if not os.path.exists(MOVIES_PATH):
    logger.info("[library.py] Movies path doesn't exist:"+MOVIES_PATH)
    os.mkdir(MOVIES_PATH)

FOLDER_TVSHOWS = "SERIES"  # config.get_localized_string(30073)
TVSHOWS_PATH = xbmc.translatePath(os.path.join(LIBRARY_PATH, FOLDER_TVSHOWS))
if not os.path.exists(TVSHOWS_PATH):
    logger.info("[library.py] Tvshows path doesn't exist:"+TVSHOWS_PATH)
    os.mkdir(TVSHOWS_PATH)

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
    path = xbmc.translatePath(os.path.join("special://masterprofile/", "sources.xml"))
    data = read_file(path)
    if "special://home/userdata/addon_data/plugin.video.pelisalacarta/library/" in data:
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
        path = xbmc.translatePath(os.path.join(TVSHOWS_PATH, tvshow))

        if not os.path.exists(path):
            logger.info("[library.py] savelibrary Creando directorio serie:"+path)
            try:
                os.mkdir(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

        temporada, capitulo = scrapertools.get_season_and_episode(item.title).split('x')
        season_episode = temporada+"x"+capitulo
        logger.info("{title} -> {name}".format(title=item.title, name=season_episode))

        filename = "{name}.strm".format(name=season_episode)

    fullfilename = os.path.join(path, filename)

    addon_name = sys.argv[0]
    if addon_name.strip() == "":
        addon_name = "plugin://plugin.video.pelisalacarta/"

    save_file('{addon}?{url}'.format(addon=addon_name, url=item.tourl()), fullfilename)

    if os.path.exists(fullfilename):
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

    if os.path.isfile(fname):
        try:
            with open(fname, "r") as f:
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
    # logger.debug("JSON-RPC: {}".format(data))

    if 'error' in data:
        logger.error("JSON-RPC: {}".format(data))

    elif 'movies' in data['result']:
        result = data['result']['movies']

    elif 'tvshows' in data['result']:
        result = data['result']['tvshows']

    elif 'episodes' in data['result']:
        result = data['result']['episodes']

    if result:
        for i in itemlist:
            for r in result:
                r_filename_aux = r['file'][:-1] if r['file'].endswith(os.sep) else r['file']
                r_filename = os.path.basename(r_filename_aux)
                if not r_filename:
                    r_filename = os.path.basename(r_filename_aux[:-1])
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
                        for c in sorted(infoLabels['cast'], key=lambda c: c["order"]):
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

    for key in dict_data.keys():
        # logger.info("key {}".format(key))
        for key2 in dict_data[key].keys():
            # logger.info("key2 {}".format(key2))
            if key2 not in carpetas_series:
                # logger.info("borro key2 {} carpeta {}".format(key2, carpetas_series))
                dict_data[key].pop(key2, None)

    json_data = jsontools.dump_json(dict_data)
    save_file(json_data, os.path.join(config.get_data_path(), TVSHOW_FILE))

    return []


def save_tvshow_in_file(item):
    """
    guarda nombre de la serie, canal y url para actualizar dentro del fichero 'series.xml'
    @type item: item
    @param item: elemento
    """
    logger.info("[library.py] save_tvshow_in_file")
    fname = os.path.join(config.get_data_path(), TVSHOW_FILE)
    dict_data = jsontools.load_json(read_file(fname))
    dict_data[item.channel][title_to_filename(item.show)] = item.url
    logger.info("dict_data {}".format(dict_data))
    json_data = jsontools.dump_json(dict_data)
    save_file(json_data, fname)


def mark_as_watched(category):
    """
    marca el capitulo como visto en la libreria de Kodi
    @type category: string
    @param category: categoria "Series" o "Cine"
    """
    logger.info("[library.py] mark_as_watched - category:{0}".format(category))
    # TODO revisar entero
    # TODO mirar como traktv para pillar la duración y establecer cuanto tiempo hay que esperar para poner el "visto"??
    # TODO establecer una opción que permita elegir el tiempo pasado??

    # se espera 5 min y luego se setea como visto
    import time
    time.sleep(300)

    # wait_video_break = 20
    # wait_video = time.time()
    #
    # if (time.time() - wait_video) < 5:
    #     xbmc.sleep((5 - int(time.time() - wait_video)) * 1000)

    # while not xbmc.Player().isPlaying():
    #     xbmc.sleep(10000)
    #     if (time.time() - wait_video) > wait_video_break: break

    if xbmc.Player().isPlaying():

        payload = {"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}

        data = get_data(payload)
        logger.info("call1 {}".format(data))

        # TODO datos actuales del reproductor tiempo y demás
        # {"jsonrpc":"2.0","method":"Player.GetProperties","params":{ "playerid": 1, "properties": ["speed", "time",
        # "totaltime", "percentage"]},"id":1}

        if data['result']:
            player_id = data['result'][0]["playerid"]
            logger.info("call1 Categoria={}".format(category))

            if category == "Series":
                payload = {"jsonrpc": "2.0", "params": {"playerid": player_id,
                                                        "properties": ["season", "episode", "file", "showtitle"]},
                           "method": "Player.GetItem", "id": "libGetItem"}
                # TODO añadir el año para sacar el filtro
                data = get_data(payload)
                logger.info("call2 {}".format(data))

                if data['result']:

                    season = data['result']['item']['season']
                    episode = data['result']['item']['episode']
                    showtitle = data['result']['item']['showtitle']

                    logger.info("titulo es {}".format(showtitle))

                    payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {
                        "filter": {"and": [{"field": "season", "operator": "is", "value": str(season)},
                                           {"field": "episode", "operator": "is", "value": str(episode)},
                                           ]},
                        "properties": ["title", "plot", "votes", "rating", "writer", "firstaired", "playcount",
                                       "runtime", "director", "productioncode", "season", "episode", "originaltitle",
                                       "showtitle", "lastplayed", "fanart", "thumbnail", "file", "resume", "tvshowid",
                                       "dateadded", "uniqueid"]}, "id": 1}

                    data = get_data(payload)
                    logger.info("call3 {}".format(data))

                    if data['result']:
                        episodeid = 0
                        logger.info("entrooo {}:{}".format(data, showtitle))
                        for d in data['result']['episodes']:
                            logger.info("show title {}".format(d['showtitle']))
                            if d['showtitle'] == showtitle:
                                logger.info("he llegado!!")
                                episodeid = d['episodeid']
                                break

                        if episodeid != 0:

                            payload = {"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {
                                "episodeid": episodeid, "playcount": 1}, "id": 1}

                            data = get_data(payload)
                            logger.info("call4 {}".format(data))

                            if data['result'] != 'OK':
                                logger.info("ERROR al poner el capitulo como visto")

            else:
                payload = {"jsonrpc": "2.0", "params": {"playerid": 1,
                                                        "properties": ["year", "file", "title", "uniqueid",
                                                                       "originaltitle"]},
                           "method": "Player.GetItem", "id": "libGetItem"}

                data = get_data(payload)
                logger.info("call2 {}".format(data))

                if data['result']:
                    title = data['result']['item']['title']
                    year = data['result']['item']['year']

                    logger.info("titulo es {}".format(title))

                    payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {
                        "filter": {"and": [{"field": "title", "operator": "is", "value": title},
                                           {"field": "year", "operator": "is", "value": str(year)}
                                           ]},
                        "properties": ["title", "plot", "votes", "rating", "writer", "playcount", "runtime",
                                       "director", "originaltitle", "lastplayed", "fanart", "thumbnail", "file",
                                       "resume", "dateadded"]}, "id": 1}

                    data = get_data(payload)
                    logger.info("call3 {}".format(data))

                    if data['result']:
                        movieid = 0
                        logger.info("entrooo {}:{}".format(data, title))
                        for d in data['result']['movies']:
                            logger.info("title {}".format(d['title']))
                            if d['title'] == title:
                                logger.info("he llegado!!")
                                movieid = d['movieid']
                                break

                        if movieid != 0:

                            payload = {"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {
                                    "movieid": movieid, "playcount": 1}, "id": 1}

                            data = get_data(payload)

                            logger.info("call4 {}".format(data))

                            if data['result'] != 'OK':
                                logger.info("ERROR al poner el capitulo como visto")


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
        response = requests.post(xbmc_json_rpc_url, data=jsontools.dump_json(payload), headers=headers)
        data = jsontools.load_json(response.text)
    else:
        data = jsontools.load_json(xbmc.executeJSONRPC(jsontools.dump_json(payload)))

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
                        if aux[2] in dict_data:
                            if aux[0] in dict_data[aux[2]]:
                                dict_data[aux[2]][aux[0]] = aux[1]
                        else:
                            dict_data = {aux[2]: {aux[0]: aux[1]}}

            except EnvironmentError:
                logger.info("ERROR al leer el archivo: {0}".format(fname))
            else:
                os.rename(os.path.join(config.get_data_path(), TVSHOW_FILE_OLD),
                          os.path.join(config.get_data_path(), "series_old.xml"))
                json_data = jsontools.dump_json(dict_data)
                save_file(json_data, os.path.join(config.get_data_path(), TVSHOW_FILE))
