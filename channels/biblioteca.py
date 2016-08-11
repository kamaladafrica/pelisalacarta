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
        if 'playcounts' in it_nfo:
            it.playcounts = it_nfo.playcounts
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

    download_path = filetools.join(config.get_library_path(), "Descargas", "Cine")
    itemlist = []

    for raiz, subcarpetas, ficheros in filetools.walk(library.MOVIES_PATH):
        for f in ficheros:
            if f.endswith(".strm"):
                strm_path = filetools.join(raiz, f)
                item_strm = Item().fromurl(filetools.read(strm_path))
                #logger.debug("item_strm: " + item_strm.tostring('\n'))
                nfo_path = os.path.splitext(strm_path)[0] + '.nfo'
                url_scraper, new_item = read_nfo(nfo_path, item_strm)

                #new_item.contentChannel = new_item.channel
                new_item.title = new_item.contentTitle


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
                    new_item.text_color = "blue"
                elif len(list_canales) > 1:
                    new_item.contentChannel = ""
                    new_item.text_color = "orange"
                else:
                    # Si no hay canales no añadimos el item
                    continue

                #logger.debug("new_item: " + new_item.tostring('\n'))
                itemlist.append(new_item)

    '''
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
    '''

    return sorted(itemlist, key=lambda it: it.title.lower())


def buscar_canales(item):
    logger.info("pelisalacarta.channels.biblioteca buscar_canales")
    #logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []
    list_canales = []
    action = "filtrar_por_canal"

    if item.contentType == "tvshow":
        action = "get_temporadas"

    for fd in filetools.listdir(item.path):
        if fd.endswith('.dat'):
            # Obtenemos el canal desde el nombre del fichero_[canal].dat
            nom_canal = os.path.basename(fd)[:-5].split('[')[1]
            if nom_canal not in list_canales:
                '''if item.contentType == 'tvshow':
                    season_episode = '%sx%s' % (item.contentSeason, str(item.contentEpisodeNumber).zfill(2))
                    if not season_episode in os.path.basename(fd):
                        # Si el .dat no pertenece al capitulo buscado nos lo saltamos
                        continue'''

                # Añadimos un item por cada uno de los canales obtenidos
                list_canales.append(nom_canal)
                itemlist.append(item.clone(contentChannel=nom_canal, action=action,
                                           title=nom_canal.capitalize(), text_color="blue"))
    return itemlist

def filtrar_por_canal(item):
    logger.info("pelisalacarta.channels.biblioteca filtrar_por_canal")
    logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []

    for fd in filetools.listdir(item.path):
        if fd.endswith('[%s].dat' %item.contentChannel):
            # Añadimos un item por cada fichero_[canal].dat
            dat_path = filetools.join(item.path, fd)
            item_dat = Item().fromurl(filetools.read(dat_path))
            #logger.debug("item_dat: " + fd + "\n" + item_dat.tostring('\n'))
            new_item = item.clone(action=item_dat.action, channel=item_dat.channel, infoLabels=item.infoLabels)
            new_item.multi= True

            # Renombrar episodios TODO ES NECESARIO?
            '''if new_item.contentType != 'movie':
                # Obtener los datos del season_episode.nfo
                nfo_path = dat_path.replace(' [%s].dat' %item.contentChannel,'.nfo')
                url_scraper, new_item = read_nfo(nfo_path, new_item)
                new_item.title = nfo_path #new_item.contentTitle'''

            itemlist.append(new_item)

    if len(itemlist) == 1 and item.contentType == 'movie':
        # Si solo hay un fichero_[canal].dat y el contenido es una pelicula
        # devolvemos el listado de enlaces a los servidores
        item = itemlist[0]
        channel = None

        # Importamos el canal
        try:
            channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
        except:
            exec "import channels." + item.channel + " as channel"

        # Ejecutamos find_videos, del canal o común
        if hasattr(channel, 'findvideos'):
            itemlist = getattr(channel, 'findvideos')(item)
        else:
            from core import servertools
            itemlist = servertools.find_video_items(item)

    return itemlist


def get_canales_movies(item):
    # TODO yo no lo uso
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
    # TODO falta añadir descargas
    logger.info("pelisalacarta.channels.biblioteca series")

    download_path = filetools.join(config.get_library_path(), "Descargas", "Series")
    itemlist = []

    # Obtenemos todos los strm de la biblioteca de SERIES recursivamente
    for raiz, subcarpetas, ficheros in filetools.walk(library.TVSHOWS_PATH):
        for f in ficheros:
            if f == "tvshow.nfo":
                tvshow_path = filetools.join(raiz, f)

                url_scraper, item_tvshow = read_nfo(tvshow_path, item)
                item_tvshow.title = item_tvshow.contentTitle
                item_tvshow.text_color = "blue"
                item_tvshow.action = "play_from_library"

                #logger.debug("item_tvshow:\n" + item_tvshow.tostring('\n'))

                list_canales = []
                for fd in filetools.listdir(raiz):
                    if fd.endswith('.dat'):
                        # Obtenemos el canal desde el nombre del fichero_[canal].dat
                        nom_canal = os.path.basename(fd)[:-5].split('[')[1]
                        if not nom_canal in list_canales:
                            list_canales.append(nom_canal)

                if len(list_canales) == 1:
                    # Si solo hay un canal no es necesario buscar mas canales
                    item_tvshow.contentChannel = list_canales[0]
                    item_tvshow.text_color = "blue"
                elif len(list_canales) > 1:
                    item_tvshow.contentChannel = ""
                    item_tvshow.text_color = "orange"
                else:
                    # Si no hay canales no añadimos el item
                    continue

                #logger.debug("item_tvshow: " + item_tvshow.tostring('\n'))
                itemlist.append(item_tvshow)
    '''
    # Obtenemos todos los videos de la biblioteca de SERIES recursivamente
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

'''
def get_canales_tvshow(item):
    logger.info("pelisalacarta.channels.biblioteca get_canales_tvshow")
    #logger.debug(item.tostring())
    itemlist = []

    # Recorremos el listado de canales
    for channel in item.list_channels:
        title = '{0} [{1}]'.format(item.contentTitle, channel["channel"])
        itemlist.append(item.clone(action='get_temporadas', title=title, path=channel['path'],
                                   contentChannel=channel["channel"], text_color="", playcounts=channel["playcounts"]))

    return sorted(itemlist, key=lambda it: it.contentChannel.lower() if not it.contentChannel == "local" else 0)
'''

def get_temporadas(item):
    logger.info("pelisalacarta.channels.biblioteca get_temporadas")
    #logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []
    dict_temp = {}

    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    if config.get_setting("no_pile_on_seasons") == "Siempre":
        return get_episodios(item)

    for f in ficheros:
        if f.endswith('[%s].dat' %item.contentChannel):
            season = f.split('x')[0]
            dict_temp[season] = "Temporada " + str(season)

    if config.get_setting("no_pile_on_seasons") == "Sólo si hay una temporada" and len(dict_temp) == 1:
        return get_episodios(item)
    else:
        # Creamos un item por cada temporada
        for season, title in dict_temp.items():
            # Marcar la temporada como vista o no
            item.infoLabels["playcount"] = item.playcounts.get("season %s" % season, 0)

            new_item = item.clone(action="get_episodios", title=title, contentTitle=title, contentSeason=season,
                                  filtrar_season=True, text_color="")

            itemlist.append(new_item)

        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))

        if config.get_setting("show_all_seasons") == "true":
            new_item = item.clone(action="get_episodios", title="*Todas las temporadas", text_color="")
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
        # strm
        if i.endswith('[%s].dat' %item.contentChannel):
            season_episode = scrapertools.get_season_and_episode(i)
            season, episode = season_episode.split("x")
            # Si hay q filtrar por temporada, ignoramos los capitulos de otras temporadas
            if item.filtrar_season and int(season) != int(item.contentSeason):
                continue

            epi = Item().fromurl(filetools.read(filetools.join(raiz, i)))
            epi.contentChannel = item.contentChannel
            epi.path = item.path #filetools.join(raiz, i)
            epi.playcounts = item.playcounts

            # Obtener los datos del season_episode.nfo
            nfo_path = filetools.join(raiz, i).replace(' [%s].dat' % item.contentChannel, '.nfo')
            url_scraper, epi = read_nfo(nfo_path, epi)

            epi.infoLabels["playcount"] = epi.playcounts.get("season %s" % season, 0)

            # Fijar el titulo del capitulo si es posible
            if epi.contentTitle:
                title_episodie = epi.contentTitle.strip()
            else:
                title_episodie = "Temporada %s Episodio %s" % (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2))

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

'''
def get_sort_temp_epi(item):
    #logger.debug(item.tostring())
    if item.infoLabels and item.infoLabels.get('season', "1") != "" and item.infoLabels.get('episode', "1") != "":
        return int(item.infoLabels.get('season', "1")), int(item.infoLabels.get('episode', "1"))
    else:
        temporada, capitulo = scrapertools.get_season_and_episode(item.title.lower()).split('x')
        return int(temporada), int(capitulo)
'''

def findvideos(item):
    logger.info("pelisalacarta.channels.biblioteca findvideos")
    canal = item.contentChannel

    channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])
    if hasattr(channel, "findvideos"):
        new_item = item.clone(channel=item.contentChannel)
        itemlist = getattr(channel, "findvideos")(new_item)
    else:
        from core import servertools
        itemlist = servertools.find_video_items(item)

    for v in itemlist:
        if v.action == "play":
            v.infoLabels = item.infoLabels
            v.contentTitle = item.contentTitle
            v.contentChannel = canal
            v.channel = "biblioteca"
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

