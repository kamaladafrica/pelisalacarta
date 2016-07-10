# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para biblioteca de pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import os

from core import config
from core import filetools
from core import logger
from core import scrapertools
from core.item import Item
from platformcode import library

DEBUG = config.get_setting("debug")

# THUMB_MOVIES = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Directors%20Chair.png"
# THUMB_TVSHOWS = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/TV%20Series.png"


def mainlist(item):
    logger.info("pelisalacarta.channels.biblioteca mainlist")

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="peliculas", title="Películas"))  #, thumbnail=THUMB_MOVIES))
    itemlist.append(Item(channel=item.channel, action="series", title="Series"))  #, thumbnail=THUMB_TVSHOWS))

    # itemlist.append(Item(channel=item.channel, title="", thumbnail=None, folder=False))
    # TODO en el caso de que no se puedan usar menus contextuales para configurar datos sobre series o peliculas
    # itemlist.append(Item(channel=item.channel, action="settings", title="Configuración", text_color="gold",
    #                      text_blod=True,
    #                      thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/thumb_configuracion.png"))

    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    strm_path = library.MOVIES_PATH
    download_path = filetools.join(config.get_library_path(), "Descargas", "Cine")

    itemlist = []

    for raiz, subcarpetas, ficheros in filetools.walk(strm_path):
        for f in ficheros:
            if f.endswith(".strm"):
                i = filetools.join(raiz, f)
                movie = Item().fromurl(filetools.read(i))
                movie.contentChannel = movie.channel
                movie.path = i
                movie.title = os.path.splitext(os.path.basename(i))[0].capitalize()
                movie.channel = "biblioteca"
                movie.action = "findvideos"
                movie.text_color = "blue"

                itemlist.append(movie)

    # Obtenemos todos los videos de la biblioteca de CINE recursivamente
    for raiz, subcarpetas, ficheros in filetools.walk(download_path):
        for f in ficheros:
            if not f.endswith(".json") and not f.endswith(".nfo")and not f.endswith(".srt"):
                i = filetools.join(raiz, f)

                movie = Item()
                movie.contentChannel = "local"
                movie.path = i
                movie.title = os.path.splitext(os.path.basename(i))[0].capitalize()
                movie.channel = "biblioteca"
                movie.action = "play"
                movie.text_color = "green"

                itemlist.append(movie)

    # library.set_infoLabels_from_library(itemlist, tipo='Movies')

    # Agrupamos las series por canales
    join_itemlist = []
    for item in itemlist:
        encontrado = False
        for unique in join_itemlist:
            if "tmdb_id" in item.infoLabels and "tmdb_id" in unique.infoLabels:
                if item.infoLabels["tmdb_id"] == unique.infoLabels["tmdb_id"]:
                    encontrado = True
                    if "list_channels" not in unique:
                        unique.list_channels = [{"path": unique.path, "channel": unique.contentChannel}]
                    unique.list_channels.append({"path": item.path, "channel": item.contentChannel})
                    unique.action = "get_canales_movies"
                    unique.text_color = "orange"

        if not encontrado:
            join_itemlist.append(item)

    return sorted(join_itemlist, key=lambda it: it.title.lower())


def get_canales_movies(item):
    logger.info("pelisalacarta.channels.biblioteca get_canales_movies")
    itemlist = []
    # Recorremos el diccionario de canales
    for channel in item.list_channels:
        if channel["channel"] == "local":
            title = '{0} [{1}]'.format(item.contentTitle, channel["channel"])
            itemlist.append(item.clone(action='play', channel="biblioteca", title=title, path=channel['path'],
                                       contentTitle=item.title, contentChannel=channel["channel"], text_color=""))
        else:
            title = '{0} [{1}]'.format(item.contentTitle, channel["channel"])
            itemlist.append(item.clone(action='findvideos', title=title, path=channel['path'],
                                       contentChannel=channel["channel"], text_color=""))

    return sorted(itemlist, key=lambda it: it.contentChannel.lower() if not it.contentChannel == "local" else 0)


def series(item):
    logger.info("pelisalacarta.channels.biblioteca series")
    strm_path = library.TVSHOWS_PATH
    download_path = filetools.join(config.get_library_path(), "Descargas", "Series")

    itemlist = []

    # Obtenemos todos los strm de la biblioteca de SERIES recursivamente
    for raiz, subcarpetas, ficheros in filetools.walk(strm_path):
        for f in ficheros:
            if f == "tvshow.json":
                i = filetools.join(raiz, f)

                tvshow = Item().fromjson(filetools.read(i))
                logger.debug(tvshow.tostring())
                tvshow.contentChannel = tvshow.channel
                tvshow.path = os.path.dirname(i)
                tvshow.title = os.path.basename(os.path.dirname(i))
                tvshow.channel = "biblioteca"
                tvshow.action = "get_temporadas"
                tvshow.text_color = "blue"

                itemlist.append(tvshow)

    # Obtenemos todos los videos de la biblioteca de CINE recursivamente
    for raiz, subcarpetas, ficheros in filetools.walk(download_path):
        for f in ficheros:
            if f == "tvshow.json":
                i = filetools.join(raiz, f)

                tvshow = Item().fromjson(filetools.read(i))
                tvshow.contentChannel = "local"
                tvshow.path = os.path.dirname(i)
                tvshow.title = os.path.basename(os.path.dirname(i))
                tvshow.channel = "biblioteca"
                tvshow.action = "get_temporadas"
                tvshow.text_color = "green"

                itemlist.append(tvshow)

    library.set_infolabels_from_library(itemlist, tipo='TVShows')

    # Agrupamos las series por canales
    join_itemlist = []
    for item in itemlist:
        encontrado = False
        for unique in join_itemlist:
            if "tmdb_id" in item.infoLabels and "tmdb_id" in unique.infoLabels:
                if item.infoLabels["tmdb_id"] == unique.infoLabels["tmdb_id"]:
                    encontrado = True
                if "list_channels" not in unique:
                    unique.list_channels = [{"path": unique.path, "channel": unique.contentChannel}]
                unique.list_channels.append({"path": item.path, "channel": item.contentChannel})
                unique.action = "get_canales_tvshow"
                unique.text_color = "orange"

        if not encontrado:
            join_itemlist.append(item)

    return sorted(join_itemlist, key=lambda it: it.title.lower())


def get_canales_tvshow(item):
    logger.info("pelisalacarta.channels.biblioteca get_canales_tvshow")
    itemlist = []

    # Recorremos el listado de canales
    for channel in item.list_channels:
        title = '{0} [{1}]'.format(item.contentTitle, channel["channel"])
        itemlist.append(item.clone(action='get_temporadas', title=title, path=channel['path'],
                                   contentChannel=channel["channel"], text_color=""))

    return sorted(itemlist, key=lambda it: it.contentChannel.lower() if not it.contentChannel == "local" else 0)


def get_temporadas(item):
    logger.info("pelisalacarta.channels.biblioteca get_temporadas")
    itemlist = []
    dict_temp = {}

    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    if config.get_setting("no_pile_on_seasons") == "Siempre":
        return get_episodios(item)

    for i in ficheros:
        if "tvshow" not in i:
            season = i.split('x')[0]
            dict_temp[season] = "Temporada " + str(season)

    if config.get_setting("no_pile_on_seasons") == "Sólo si hay una temporada" and len(dict_temp) == 1:
        return get_episodios(item)
    else:
        # Creamos un item por cada temporada
        for season, title in dict_temp.items():
            new_item = item.clone(action="get_episodios", title=title, contentTitle=title, contentSeason=season,
                                  contentEpisodeNumber="", filtrar_season=True, text_color="")
            itemlist.append(new_item)
            # logger.debug(new_item.tostring())

        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))
        if config.get_setting("show_all_seasons") == "true":
            new_item = item.clone(action="get_episodios", title="*Todas las temporadas", text_color="")
            itemlist.insert(0, new_item)

    return itemlist


def get_episodios(item):
    logger.info("pelisalacarta.channels.biblioteca get_episodios")
    itemlist = []

    # Obtenemos los archivos de los episodios
    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    # Crear un item en la lista para cada strm encontrado
    for i in ficheros:
        # strm
        if i.endswith(".strm"):
            season, episode = scrapertools.get_season_and_episode(i).split("x")
            # Si hay q filtrar por temporada, ignoramos los capitulos de otras temporadas
            if item.filtrar_season and int(season) != int(item.contentSeason):
                continue

            epi = Item().fromurl(filetools.read(filetools.join(raiz, i)))
            epi.contentChannel = item.contentChannel
            epi.path = filetools.join(raiz, i)
            epi.title = i
            epi.channel = "biblioteca"
            epi.action = "findvideos"
            epi.contentEpisodeNumber = episode
            epi.contentSeason = season

            itemlist.append(epi)

        # videos
        elif not i.endswith(".nfo") and not i.endswith(".json") and not i.endswith(".srt"):
            season, episode = scrapertools.get_season_and_episode(i).split("x")
            # Si hay q filtrar por temporada, ignoramos los capitulos de otras temporadas
            if item.filtrar_season and int(season) != int(item.contentSeason):
                continue

            epi = Item()
            epi.contentChannel = "local"
            epi.path = filetools.join(raiz, i)
            epi.title = i
            epi.channel = "biblioteca"
            epi.action = "play"
            epi.contentEpisodeNumber = episode
            epi.contentSeason = season

            itemlist.append(epi)

    library.set_infolabels_from_library(itemlist, tipo="Episodes")
    return sorted(itemlist, key=get_sort_temp_epi)


def get_sort_temp_epi(item):
    # logger.debug(item.tostring())
    if item.infoLabels and item.infoLabels.get('season', "1") != "" and item.infoLabels.get('episode', "1") != "":
        return int(item.infoLabels.get('season', "1")), int(item.infoLabels.get('episode', "1"))
    else:
        temporada, capitulo = scrapertools.get_season_and_episode(item.title.lower()).split('x')
        return int(temporada), int(capitulo)


def findvideos(item):
    logger.info("pelisalacarta.channels.biblioteca findvideos")

    channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])
    if hasattr(channel, "findvideos"):
        itemlist = getattr(channel, "findvideos")(item)
    else:
        from core import servertools
        itemlist = servertools.find_video_items(item)

    for v in itemlist:
        if v.action == "play":
            v.infoLabels = item.infoLabels
            v.contentChannel = v.channel
            v.contentTitle = item.contentTitle
            v.channel = "biblioteca"
            v.contentChannel = item.contentChannel
            v.path = item.path

    return itemlist


def play(item):
    logger.info("pelisalacarta.channels.biblioteca play")

    if not item.contentChannel == "local":
        channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])
        if hasattr(channel, "play"):
            itemlist = getattr(channel, "play")(item)
        else:
            itemlist = [item.clone()]
    else:
        itemlist = [item.clone(url=item.path, server="local")]

    library.mark_as_watched(item)

    for v in itemlist:
        v.infoLabels = item.infoLabels
        v.title = item.contentTitle
        v.thumbnail = item.thumbnail
        v.contentThumbnail = item.thumbnail

    return itemlist
