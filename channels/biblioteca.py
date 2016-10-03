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
    itemlist.append(Item(channel=item.channel, action="peliculas", title="Películas",
                         thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/thumb_biblioteca_peliculas.png"))
    itemlist.append(Item(channel=item.channel, action="series", title="Series",
                         thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/thumb_biblioteca_series.png"))

    return itemlist


def read_nfo(path_nfo, item=None):
    url_scraper = ""
    it = None
    if filetools.exists(path_nfo):
        url_scraper = filetools.read(path_nfo, 0, 1)

        if item:
            it = item.clone()
            it_nfo = Item().fromjson(filetools.read(path_nfo, 1))
            it.infoLabels = it_nfo.infoLabels
            if 'library_playcounts' in it_nfo:
                it.library_playcounts = it_nfo.library_playcounts
            if it_nfo.path:
                it.path = it_nfo.path
        else:
            it = Item().fromjson(filetools.read(path_nfo, 1))

        if 'fanart' in it.infoLabels: # it.fanart = it.infoLabels.get('fanart', "")
            it.fanart = it.infoLabels['fanart']


    return url_scraper, it


def peliculas(item):
    # TODO falta añadir descargas
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    itemlist = []

    for raiz, subcarpetas, ficheros in filetools.walk(library.MOVIES_PATH):
        for f in ficheros:
            if f.endswith(".nfo"):
                nfo_path = filetools.join(raiz, f)
                url_scraper, new_item = read_nfo(nfo_path)

                new_item.nfo = nfo_path
                new_item.thumbnail = new_item.contentThumbnail
                new_item.text_color = "blue"
                visto = new_item.library_playcounts.get(os.path.splitext(f)[0], 0)
                new_item.infoLabels["playcount"] = visto

                if visto > 0:
                    texto = "Marcar como no visto"
                    contador = 0
                else:
                    texto = "Marcar como visto"
                    contador = 1

                new_item.context = [{"title":texto,
                                     "action":"mark_content_as_watched",
                                     "channel":"biblioteca",
                                     "playcount":contador},
                                    {"title": "Eliminar (PENDIENTE)",
                                     "action": "eliminar",
                                     "channel": "biblioteca"},
                                    {"title": "Cambiar contenido (PENDIENTE)",
                                     "action": "",
                                     "channel": "biblioteca"}]

                # Opcion colorear si hay mas de un canal
                '''
                list_canales = []
                for fd in filetools.listdir(raiz):
                    if fd.endswith('.json'):
                        # Obtenemos el canal desde el nombre del fichero_[canal].json
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


                #logger.debug("new_item: " + new_item.tostring('\n'))
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

    # Obtenemos todos los tvshow.nfo de la biblioteca de SERIES recursivamente
    for raiz, subcarpetas, ficheros in filetools.walk(library.TVSHOWS_PATH):
        for f in ficheros:
            if f == "tvshow.nfo":
                tvshow_path = filetools.join(raiz, f)
                logger.debug(tvshow_path)
                url_scraper, item_tvshow = read_nfo(tvshow_path)
                item_tvshow.title = item_tvshow.contentTitle
                item_tvshow.text_color = "0xFFDF7401" # TODO Opcionalmente podemos cambiar color si hay mas de un canal
                item_tvshow.path = raiz
                item_tvshow.nfo = tvshow_path

                # Menu contextual: Buscar automáticamente nuevos episodios o no
                if item_tvshow.active:
                    texto = "No buscar automáticamente nuevos episodios"
                    value = False
                else:
                    texto = "Buscar automáticamente nuevos episodios"
                    value = True

                item_tvshow.context = [{"title": texto,
                                        "action": "mark_tvshow_as_updatable",
                                        "channel": "biblioteca",
                                        "active": value},
                                        {"title": "Eliminar (PENDIENTE)",
                                        "action": "eliminar",
                                        "channel": "biblioteca"},
                                        {"title": "Cambiar contenido (PENDIENTE)",
                                        "action": "",
                                        "channel": "biblioteca"}]

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
    #logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []
    dict_temp = {}

    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    if config.get_setting("no_pile_on_seasons") == "Siempre":
        return get_episodios(item)

    for f in ficheros:
        if f.endswith('.json'):
            season = f.split('x')[0]
            dict_temp[season] = "Temporada " + str(season)

    if config.get_setting("no_pile_on_seasons") == "Sólo si hay una temporada" and len(dict_temp) == 1:
        return get_episodios(item)
    else:
        # Creamos un item por cada temporada
        for season, title in dict_temp.items():
            new_item = item.clone(action="get_episodios", title=title, contentSeason=season,
                                  filtrar_season=True)

            # Menu contextual: Releer tvshow.nfo
            url_scraper, item_nfo = read_nfo(item.nfo)

            # Menu contextual: Marcar la temporada como vista o no
            visto = item_nfo.library_playcounts.get("season %s" % season, 0)
            new_item.infoLabels["playcount"] = visto
            if visto > 0:
                texto = "Marcar como no vista"
                value = 0
            else:
                texto = "Marcar como vista"
                value = 1
            new_item.context = [{"title": texto,
                                 "action": "mark_season_as_watched",
                                 "channel": "biblioteca",
                                 "playcount": value}]


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
    #logger.debug("item:\n" + item.tostring('\n'))
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
            url_scraper, epi = read_nfo(nfo_path)

            # Fijar el titulo del capitulo si es posible
            if epi.contentTitle:
                title_episodie = epi.contentTitle.strip()
            else:
                title_episodie = "Temporada %s Episodio %s" % (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2))

            epi.contentTitle = "%sx%s" %(epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2))
            epi.title = "%sx%s - %s" % (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2), title_episodie)

            # Menu contextual: Releer tvshow.nfo
            url_scraper, item_nfo = read_nfo(item.nfo)

            # Menu contextual: Marcar episodio como visto o no
            visto = item_nfo.library_playcounts.get(season_episode, 0)
            epi.infoLabels["playcount"] = visto
            if visto > 0:
                texto = "Marcar como no visto"
                value = 0
            else:
                texto = "Marcar como visto"
                value = 1
            epi.context = [{"title": texto,
                            "action": "mark_content_as_watched",
                            "channel": "biblioteca",
                            "playcount": value,
                            "nfo":item.nfo}]

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
    logger.debug("item:\n" + item.tostring('\n'))

    itemlist = []
    list_canales = {}

    if not item.contentTitle or not item.strm_path:
        logger.debug("No se pueden buscar videos por falta de parametros")
        return []

    contentTitle = filter(lambda c: c not in ":*?<>|\/", item.contentTitle).strip().lower()

    if item.contentType == 'movie':
        item.strm_path = filetools.join(library.MOVIES_PATH, item.strm_path.strip('\/'))

        path_dir = os.path.dirname(item.strm_path)
        item.nfo = filetools.join(path_dir, os.path.basename(path_dir) + ".nfo")
    else:
        item.strm_path = filetools.join(library.TVSHOWS_PATH, item.strm_path.strip('\/'))
        path_dir = os.path.dirname(item.strm_path)
        item.nfo = filetools.join(path_dir, 'tvshow.nfo')

    for fd in filetools.listdir(path_dir):
        if fd.endswith('.json'):
            contenido,nom_canal = fd[:-6].split('[')
            if (contentTitle in contenido.strip() or item.contentType == 'movie') and nom_canal not in list_canales.keys():
                list_canales[nom_canal] = filetools.join(path_dir,fd)

    filtro_canal = ''
    if len(list_canales) > 1 and config.get_setting("ask_channel") == "true":
        from platformcode import platformtools
        opciones = ["Mostrar solo los enlaces de %s" %k.capitalize() for k in list_canales.keys()]
        opciones.insert(0,"Mostrar todos los enlaces")
        index = platformtools.dialog_select(config.get_localized_string(30163), opciones)
        if index < 0:
            return []
        if index > 0:
            filtro_canal = opciones[index]


    for nom_canal, json_path in list_canales.items():
        if filtro_canal and filtro_canal != nom_canal.capitalize():
            continue

        # TODO lo siguiente podriamos hacerlo multihilo
        # Importamos el canal de la parte seleccionada
        try:
            channel = __import__('channels.%s' % nom_canal,
                                 fromlist=["channels.%s" % nom_canal])
        except:
            exec "import channels." + nom_canal + " as channel"

        item_json = Item().fromjson(filetools.read(json_path))

        # Ejecutamos find_videos, del canal o común
        if hasattr(channel, 'findvideos'):
            list_servers = getattr(channel, 'findvideos')(item_json)
        else:
            from core import servertools
            list_servers = servertools.find_video_items(item_json)

        # Cambiarle el titulo a los servers añadiendoles el nombre del canal delante y
        # las infoLabels y las imagenes del item si el server no tiene
        for server in list_servers:
            if not server.action: # Ignorar las etiquetas
                continue

            # TODO Opcionalmente podriamos alternar entre varios colores (cada canal de un color)
            server.contentChannel = server.channel
            server.channel = "biblioteca"
            server.nfo = item.nfo
            server.strm_path = item.strm_path
            server.title = "%s: %s" %(nom_canal.capitalize(),server.title)

            #if len(server.infoLabels) <= len(item.infoLabels):
            server.infoLabels = item.infoLabels

            if not server.thumbnail:
                server.thumbnail = item.thumbnail

            #logger.debug(server.tostring('\n'))
            itemlist.append(server)


    #return sorted(itemlist, key=lambda it: it.title.lower())
    return itemlist


def play(item):
    logger.info("pelisalacarta.channels.biblioteca play")
    #logger.debug("item:\n" + item.tostring('\n'))

    if not item.contentChannel == "local":
        channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])
        if hasattr(channel, "play"):
            itemlist = getattr(channel, "play")(item)

        else:
            itemlist = [item.clone()]
    else:
        itemlist = [item.clone(url=item.strm_path, server="local")]

    #library.mark_auto_as_watched(item)

    # Esto es necesario por si el play del canal elimina los datos
    for v in itemlist:
        v.nfo = item.nfo
        v.strm_path = item.strm_path
        v.infoLabels = item.infoLabels
        v.title = item.contentTitle
        v.thumbnail = item.thumbnail
        v.contentThumbnail = item.thumbnail

    return itemlist




# metodos de menu contextual
def mark_content_as_watched(item):
    logger.info("pelisalacarta.channels.biblioteca mark_content_as_watched")
    library.mark_content_as_watched(item, item.playcount)


def mark_season_as_watched(item):
    logger.info("pelisalacarta.channels.biblioteca mark_season_as_watched")
    library.mark_season_as_watched(item, item.playcount)


def mark_tvshow_as_updatable(item):
    logger.info("pelisalacarta.channels.biblioteca mark_tvshow_as_updatable")
    library.mark_tvshow_as_updatable(item, item.active)


def eliminar(item):
    logger.info("pelisalacarta.channels.biblioteca eliminar")
    library.delete(item)
