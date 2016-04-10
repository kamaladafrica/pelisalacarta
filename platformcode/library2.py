# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Herramientas de integración en Librería
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import errno
import os
import re
import sys
import string
import urllib
import xbmc

from core import config
from core.item import Item
from core import jsontools
from core import logger
# TODO EVITAR USAR REQUESTS
from lib import requests

allchars = string.maketrans('', '')
deletechars = '\\/:*"<>|?'  # Caracteres no válidos en nombres de archivo

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

# MOVIES_PATH
# TODO elegir el nombre de la carpeta o ruta???
FOLDER_MOVIES = "CINE"  # config.get_localized_string(30072)
MOVIES_PATH = xbmc.translatePath(os.path.join(LIBRARY_PATH, FOLDER_MOVIES))
if not os.path.exists(MOVIES_PATH):
    logger.info("[library2.py] Movies path doesn't exist:"+MOVIES_PATH)
    os.mkdir(MOVIES_PATH)

# TVSHOWS_PATH
FOLDER_TVSHOWS = "SERIES"  # config.get_localized_string(30073)
TVSHOWS_PATH = xbmc.translatePath(os.path.join(LIBRARY_PATH, FOLDER_TVSHOWS))
if not os.path.exists(TVSHOWS_PATH):
    logger.info("[library2.py] Tvshows path doesn't exist:"+TVSHOWS_PATH)
    os.mkdir(TVSHOWS_PATH)

# Versions compatible with JSONRPC v6
LIST_PLATFORM_COMPATIBLE = ["xbmc-frodo", "xbmc-gotham", "kodi-helix", "kodi-isengard", "kodi-jarvis"]


def is_compatible():
    logger.info("[library2.py] is_compatible")
    if config.get_platform() in LIST_PLATFORM_COMPATIBLE and library_in_kodi():
        return True
    else:
        return False


def library_in_kodi():
    logger.info("[library2.py] library_in_kodi")
    path = xbmc.translatePath(os.path.join("special://masterprofile/", "sources.xml"))
    data = read_file(path)
    if "special://home/userdata/addon_data/plugin.video.pelisalacarta/library/" in data:
        return True
    else:
        return False


# TODO hacerlo más limpio
def elimina_tildes(s):
    s = s.replace("Á", "a")
    s = s.replace("É", "e")
    s = s.replace("Í", "i")
    s = s.replace("Ó", "o")
    s = s.replace("Ú", "u")
    s = s.replace("á", "a")
    s = s.replace("é", "e")
    s = s.replace("í", "i")
    s = s.replace("ó", "o")
    s = s.replace("ú", "u")
    s = s.replace("À", "a")
    s = s.replace("È", "e")
    s = s.replace("Ì", "i")
    s = s.replace("Ò", "o")
    s = s.replace("Ù", "u")
    s = s.replace("à", "a")
    s = s.replace("è", "e")
    s = s.replace("ì", "i")
    s = s.replace("ò", "o")
    s = s.replace("ù", "u")
    s = s.replace("ç", "c")
    s = s.replace("Ç", "C")
    s = s.replace("Ñ", "n")
    s = s.replace("ñ", "n")
    return s


def title_to_folder_name(title):
    logger.info("folder_name="+title)
    folder_name = elimina_tildes(title)
    logger.info("folder_name="+folder_name)
    folder_name = string.translate(folder_name, allchars, deletechars)
    logger.info("folder_name="+folder_name)
    return folder_name


def savelibrary(item):
    logger.info("[library2.py] savelibrary")

    path = LIBRARY_PATH
    filename = ""

    # MOVIES
    if item.category == "Cine":  # config.get_localized_string(30072):
        path = MOVIES_PATH
        filename = string.translate(item.fulltitle, allchars, deletechars)+".strm"
    # TVSHOWS
    elif item.category == "Series":  # config.get_localized_string(30073):
        path = TVSHOWS_PATH

        if item.show != "":
            tvshow = title_to_folder_name(item.show)
            path = xbmc.translatePath(os.path.join(TVSHOWS_PATH, tvshow))

        if not os.path.exists(path):
            logger.info("[library2.py] savelibrary Creando directorio serie:"+path)
            try:
                os.mkdir(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

        patron = "(\d+)[x|X](\d+)"
        matches = re.compile(patron).findall(item.title)
        season_episode = matches[0][0]+"x"+matches[0][1]
        logger.info("{title} -> {name}".format(title=item.title, name=season_episode))

        filename = "{name}.strm".format(name=season_episode)

    fullfilename = os.path.join(path, filename)

    addon_name = sys.argv[0]
    if addon_name.strip() == "":
        addon_name = "plugin://plugin.video.pelisalacarta/"

    # TODO arreglar esto
    # itemurl = "{addon}?channel={channel}&action={action}&category={category}&title={title}&url={url}&" \
    #           "thumbnail={thumb}&plot={plot}&server={server}&show={show}&subtitle={subtitle}"\
    #     .format(addon=addon_name, channel=item.channel(), action=item.action, category=urllib.quote_plus(item.category),
    #             title=urllib.quote_plus(item.title), url=urllib.quote_plus(item.url),
    #             thumb=urllib.quote_plus(item.thumbnail), plot=urllib.quote_plus(item.plot), server=item.server,
    #             show=item.show, subtitle=urllib.quote_plus(item.subtitle))  # , extra=urllib.quote_plus(extra))
    itemurl = '%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&server=%s&Serie=%s' \
              '&subtitle=%s&extra=%s' % (addon_name, item.channel, item.action, urllib.quote_plus(item.category),
                                         urllib.quote_plus(item.title), urllib.quote_plus(item.url), "", "",
                                         item.server, item.show, urllib.quote_plus(item.subtitle),
                                         urllib.quote_plus(item.extra))
    save_strm(fullfilename, itemurl)

    if os.path.exists(fullfilename):
        logger.info("[library2.py] savelibrary el fichero existe. Se sobreescribe")
        nuevo = 0
    else:
        nuevo = 1

    logger.info("[library2.py] savelibrary - Fin")

    return nuevo


def read_file(fname):
    """
    pythonic way to read from file
    :param: fname:
    :return: data
    :rtype: string
    """
    logger.info("[library2.py] read_file")
    data = ""

    if os.path.isfile(fname):
        try:
            with open(fname, "r") as f:
                for line in f:
                    data += line
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: {0}".format(fname))

    # logger.info("[library2.py] read_file-data {0}".format(data))
    return data


def save_strm(fname, data):
    logger.info("[library2.py] save_strm")
    logger.info("default encoding: {0}".format(sys.getdefaultencoding()))
    try:
        with open(fname, "w") as f:
            try:
                f.write(data)
            except UnicodeEncodeError:
                logger.info("Error al realizar el encode, se usa uft8")
                f.write(data.encode('utf-8'))
    except EnvironmentError:
        logger.info("[library2.py] save_strm - Error al guardar el archivo: {file}".format(file))
        return False

    return True


def get_movies(item):
    logger.info("[library2.py] get_movies")
    path = MOVIES_PATH

    itemlist = []

    aux_list = next(os.walk(path))[item.element]
    for i in aux_list:
        itemlist.append(Item(channel=item.channel, action=item.action, title=i, element=2, path=i))

    return itemlist


def get_tvshows(item):
    logger.info("[library2.py] get_tvshows")
    path = TVSHOWS_PATH

    itemlist = []

    if item.element != 1:
        path = os.path.join(path, item.path)
    aux_list = next(os.walk(path))[item.element]
    for i in aux_list:
        url = ""
        folder = True
        channel = item.channel
        if ".strm" in i:
            data = read_file(os.path.join(path, i))
            begin = data.find("channel=")
            end = data.find("&", begin)
            channel = data[begin+8:end]
            channel = urllib.unquote_plus(channel)

            begin = data.find("url=")
            end = data.find("&", begin)
            url = data[begin+4:end]
            url = urllib.unquote_plus(url)
            folder = False

        itemlist.append(Item(channel=channel, action=item.action, title=i, element=2, path=i, url=url,
                             folder=folder))

    return itemlist


def tvshows_file(item):
    logger.info("[library2.py] tvshows_file")

    itemlist = []

    tvshow_file = os.path.join(config.get_library_path(), "series.xml")
    if not os.path.exists(tvshow_file):
        tvshow_file = os.path.join(config.get_data_path(), "series.xml")

    logger.info("leer el archivo: {0}".format(tvshow_file))

    try:
        with open(tvshow_file, "r") as f:
            for line in f:
                aux = line.rstrip('\n').split(",")
                logger.info("archivo: {0}".format(aux))
                itemlist.append(Item(channel=item.channel, action=item.action, title="[{channel}] {show}"
                                     .format(channel=aux[2], show=aux[0])))
    except EnvironmentError:
        logger.info("ERROR al leer el archivo: {0}".format(tvshow_file))
        return []

    return itemlist


def save_tvshow_in_file_xml(item):
    # Lista con series para actualizar
    nombre_fichero_config_canal = os.path.join(config.get_library_path(), "series.xml")
    if not os.path.exists(nombre_fichero_config_canal):
        nombre_fichero_config_canal = os.path.join(config.get_data_path(), "series.xml")
    logger.info("nombre_fichero_config_canal=" + nombre_fichero_config_canal)
    if not os.path.exists(nombre_fichero_config_canal):
        f = open(nombre_fichero_config_canal, "w")
    else:
        f = open(nombre_fichero_config_canal, "r")
        contenido = f.read()
        f.close()
        f = open(nombre_fichero_config_canal, "w")
        f.write(contenido)
    f.write(title_to_folder_name(item.show) + "," + item.url + "," + item.channel + "\n")
    f.close()


def mark_as_watched(category):
    logger.info("[library2.py] mark_as_watched - category:{cat}".format(cat=category))


    # TODO mirar como lo hace traktv para pillar la duración y establecer cuanto tiempo hay que esperar para poner el "visto"??
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
        # {"jsonrpc":"2.0","method":"Player.GetProperties","params":{ "playerid": 1, "properties": ["speed", "time", "totaltime", "percentage"]},"id":1}

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
    # Required header for XBMC JSON-RPC calls, otherwise you'll get a 415 HTTP response code - Unsupported media type
    headers = {'content-type': 'application/json'}

    if modo_cliente:
        response = requests.post(xbmc_json_rpc_url, data=jsontools.dump_json(payload), headers=headers)
        data = jsontools.load_json(response.text)
    else:
        data = jsontools.load_json(xbmc.executeJSONRPC(jsontools.dump_json(payload)))
    return data
