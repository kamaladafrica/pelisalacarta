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


def mainlist(item):
    logger.info("pelisalacarta.channels.biblioteca mainlist")

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="peliculas", title="Películas"))
    itemlist.append(Item(channel=item.channel, action="series", title="Series"))

    return itemlist


def read_nfo(path_nfo, item):
    url_scraper = ""
    it = None
    if filetools.exists(path_nfo):
        url_scraper = filetools.read(path_nfo, 0, 1)
        it_nfo = Item().fromjson(filetools.read(path_nfo,1))
        it = item.clone()
        it.infoLabels = it_nfo.infoLabels
        if 'library_playcounts' in it_nfo:
            it.library_playcounts = it_nfo.library_playcounts
        it.nfo = path_nfo
        if 'fanart' in it.infoLabels: # it.fanart = it.infoLabels.get('fanart', "")
            it.fanart = it.infoLabels['fanart']
        if it.contentThumbnail:
            it.thumbnail = it.contentThumbnail
        if it_nfo.path:
            it.path = it_nfo.path

    return url_scraper, it


def peliculas(item):
    # TODO falta añadir descargas
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    itemlist = []

    for raiz, subcarpetas, ficheros in filetools.walk(library.MOVIES_PATH):
        for f in ficheros:
            if f.endswith(".nfo"):
                nfo_path = filetools.join(raiz, f)
                url_scraper, new_item = read_nfo(nfo_path, item)
                new_item.title = new_item.contentTitle
                new_item.path = raiz
                new_item.action = 'findvideos'
                new_item.text_color = "blue"
                new_item.infoLabels["playcount"] = new_item.library_playcounts.get(new_item.contentTitle.lower(), 0)

                # Opcion colorear si hay mas de un canal
                '''
                list_canales = []
                for fd in filetools.listdir(raiz):
                    if fd.endswith('.dat'):
                        # Obtenemos el canal desde el nombre del fichero_[canal].dat
                        nom_canal = os.path.basename(fd)[:-5].split('[')[1]
                        if not nom_canal in list_canales:
                            list_canales.append(nom_canal)

                if len(list_canales) == 1:
                    # Si solo hay un canal no es necesario buscar mas canales
                    new_item.contentChannel = list_canales[0]

                elif len(list_canales) > 1:
                    new_item.contentChannel = ""
                    new_item.text_color = "orange"
                else:
                    # Si no hay canales no añadimos el item
                    continue
                '''

                logger.debug("new_item: " + new_item.tostring('\n'))
                logger.debug(str(type(new_item.infoLabels)))
                itemlist.append(new_item)

    '''
    # Obtenemos todos los videos de la biblioteca de CINE recursivamente
    download_path = filetools.join(config.get_library_path(), "Descargas", "Cine")
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
    '''

    return sorted(itemlist, key=lambda it: it.title.lower())


def series(item):
    # TODO falta añadir descargas
    logger.info("pelisalacarta.channels.biblioteca series")
    itemlist = []

    logger.debug("prueba:" + str(type(item.infoLabels)))

    # Obtenemos todos los tvshow.nfo de la biblioteca de SERIES recursivamente
    for raiz, subcarpetas, ficheros in filetools.walk(library.TVSHOWS_PATH):
        for f in ficheros:
            if f == "tvshow.nfo":
                tvshow_path = filetools.join(raiz, f)
                url_scraper, item_tvshow = read_nfo(tvshow_path, item)
                item_tvshow.title = item_tvshow.contentTitle
                item_tvshow.path = raiz
                item_tvshow.action = "get_temporadas"
                item_tvshow.text_color = "blue"

                # TODO Opcionalmente podemos colorear si hay mas de un canal

                #logger.debug("item_tvshow:\n" + item_tvshow.tostring('\n'))
                itemlist.append(item_tvshow)


    '''
       # Obtenemos todos los videos de la biblioteca de SERIES recursivamente
       download_path = filetools.join(config.get_library_path(), "Descargas", "Series")
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
       '''

    return sorted(itemlist, key=lambda it: it.title.lower())


def get_temporadas(item):
    logger.info("pelisalacarta.channels.biblioteca get_temporadas")
    logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []
    dict_temp = {}

    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    if config.get_setting("no_pile_on_seasons") == "Siempre":
        return get_episodios(item)

    for f in ficheros:
        if f.endswith('.dat'):
            season = f.split('x')[0]
            dict_temp[season] = "Temporada " + str(season)

    if config.get_setting("no_pile_on_seasons") == "Sólo si hay una temporada" and len(dict_temp) == 1:
        return get_episodios(item)
    else:
        # Creamos un item por cada temporada
        for season, title in dict_temp.items():
            # Marcar la temporada como vista o no
            item.infoLabels["playcount"] = item.library_playcounts.get("season %s" % season, 0)

            new_item = item.clone(action="get_episodios", title=title, contentSeason=season,
                                  filtrar_season=True)
            #logger.debug("new_item:\n" + new_item.tostring('\n'))
            itemlist.append(new_item)

        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))

        if config.get_setting("show_all_seasons") == "true":
            new_item = item.clone(action="get_episodios", title="*Todas las temporadas")
            new_item.infoLabels["playcount"] = 0
            itemlist.insert(0, new_item)

    return itemlist


def get_episodios(item):
    logger.info("pelisalacarta.channels.biblioteca get_episodios")
    logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []
    episodes_wathed = []

    # Obtenemos los archivos de los episodios
    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    # Crear un item en la lista para cada strm encontrado
    for i in ficheros:
        if i.endswith('.strm'):
            season_episode = scrapertools.get_season_and_episode(i)
            season, episode = season_episode.split("x")
            # Si hay q filtrar por temporada, ignoramos los capitulos de otras temporadas
            if item.filtrar_season and int(season) != int(item.contentSeason):
                continue


            # Obtener los datos del season_episode.nfo
            nfo_path = filetools.join(raiz, i).replace('.strm', '.nfo')
            url_scraper, epi = read_nfo(nfo_path, item)
            #logger.debug("epi:\n" + epi.tostring('\n'))

            epi.action = 'findvideos'
            epi.infoLabels["playcount"] = epi.library_playcounts.get(season_episode, 0)

            # Fijar el titulo del capitulo si es posible
            if epi.contentTitle:
                title_episodie = epi.contentTitle.strip()
            else:
                title_episodie = "Temporada %s Episodio %s" % (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2))

            epi.contentTitle = "%sx%s" %(epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2))
            epi.title = "%sx%s - %s" % (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2), title_episodie)

            #logger.debug("epi:\n" + epi.tostring('\n'))
            itemlist.append(epi)


        # videos TODO
        '''elif not i.endswith(".nfo") and not i.endswith(".json") and not i.endswith(".srt"):
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

            itemlist.append(epi)'''

    return sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))


def findvideos(item):
    logger.info("pelisalacarta.channels.biblioteca findvideos")
    #logger.debug("item:\n" + item.tostring('\n'))
    logger.debug(str(type(item.infoLabels)))
    itemlist = []
    list_canales = {}

    if not item.contentTitle or not item.path:
        logger.debug("No se pueden buscar videos por falta de parametros")
        return []

    for fd in filetools.listdir(item.path):
        if fd.endswith('.dat'):
            contenido,nom_canal = fd[:-5].split('[')
            #logger.debug(contenido)
            contentTitle = filter(lambda c: c not in ":*?<>|\/", item.contentTitle).strip().lower()
            #logger.debug(contentTitle)

            if contentTitle in contenido.strip() and nom_canal not in list_canales.keys():
                list_canales[nom_canal] = filetools.join(item.path,fd)

    #logger.debug(str(list_canales))
    for nom_canal, dat_path in list_canales.items():
        # TODO lo siguiente podriamos hacerlo multihilo
        # Importamos el canal de la parte seleccionada
        try:
            channel = __import__('channels.%s' % nom_canal,
                                 fromlist=["channels.%s" % nom_canal])
        except:
            exec "import channels." + nom_canal + " as channel"

        item_dat = Item().fromurl(filetools.read(dat_path))

        # Ejecutamos find_videos, del canal o común
        if hasattr(channel, 'findvideos'):
            list_servers = getattr(channel, 'findvideos')(item_dat)
        else:
            from core import servertools
            list_servers = servertools.find_video_items(item_dat)

        if len(list_canales) > 1:
            # Cambiarle el titulo a los servers añadiendoles el nombre del canal delante y
            # las infoLabels y las imagenes del item si el server no tiene
            for server in list_servers:
                '''if not server.action:
                    continue'''

                server.title = "%s: %s" %(nom_canal.capitalize(),server.title)

                if not server.infoLabels:
                    server.infoLabels = item.infoLabels

                if not server.thumbnail:
                    server.thumbnail = item.thumbnail


                #logger.debug(server.tostring('\n'))
                itemlist.append(server)
        else:
            itemlist.extend(list_servers)

    #return sorted(itemlist, key=lambda it: it.title.lower())
    return itemlist


# TODO probar esto
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




# metodos de menu contextual
def marcar_episodio(item):
    logger.info("pelisalacarta.channels.biblioteca marcar_episodio")

    library.marcar_episodio(item)


def marcar_temporada(item):
    logger.info("pelisalacarta.channels.biblioteca marcar_temporada")

    item = library.marcar_temporada(item)

    item.action = "get_temporadas"
    get_temporadas(item)


def actualizacion_automatica(item):
    logger.info("pelisalacarta.channels.biblioteca actualizacion_automatica")
    logger.info("item:{}".format(item.tostring()))

    library.actualizacion_automatica(item)


def eliminar(item):
    logger.info("pelisalacarta.channels.biblioteca eliminar")
    logger.info("item:{}".format(item.tostring()))

    library.delete(item)

