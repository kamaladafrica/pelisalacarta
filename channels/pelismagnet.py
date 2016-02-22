# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para pelismagnet
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import re

from core import logger
from core import scrapertools
from core.item import Item

from core import jsontools

__channel__ = "pelismagnet"
__category__ = "F,S,D"
__type__ = "generic"
__title__ = "Pelis Magnet"
__language__ = "ES"

host = 'http://pelismag.net'
api = host + '/api'
api_serie = host + "/seapi"
api_temp = host + "/sapi"


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.pelismagnet mainlist")

    itemlist = list()
    itemlist.append(Item(channel=__channel__, action="pelis", title="[B]Peliculas[/B]",
                         url=api + "?sort_by=''&page=0"))
    itemlist.append(Item(channel=__channel__, action="pelis", title="     Estrenos",
                         url=api + "?sort_by=date_added&page=0"))
    itemlist.append(Item(channel=__channel__, action="pelis", title="     + Populares", url=api + "?page=0"))
    itemlist.append(Item(channel=__channel__, action="pelis", title="     + Valoradas",
                         url=api + "?sort_by=rating&page=0"))
    itemlist.append(Item(channel=__channel__, action="search", title="     Buscar...", url=api + "?keywords=%s&page=0"))
    itemlist.append(Item(channel=__channel__, action="series", title="[B]Series[/B]",
                         url=api_serie + "?sort_by=''&page=0"))
    itemlist.append(Item(channel=__channel__, action="series", title="     Recientes",
                         url=api_serie + "?sort_by=date_added&page=0"))
    itemlist.append(Item(channel=__channel__, action="series", title="     + Populares", url=api_serie + "?page=0"))
    itemlist.append(Item(channel=__channel__, action="series", title="     + Valoradas",
                         url=api_serie + "?sort_by=rating&page=0"))
    itemlist.append(Item(channel=__channel__, action="search", title="     Buscar...",
                         url=api_serie + "?keywords=%s&page=0"))
    return itemlist


def series(item):
    logger.info("pelisalacarta.pelismagnet series")
    itemlist = []

    data = scrapertools.cachePage(item.url)
    lista = jsontools.load_json(data)

    for i in lista:

        punt = i.get("puntuacio", "")
        valoracion = ""
        if punt and not 0:
            valoracion = "  (Val: {punt})".format(punt=punt)

        title = "{nombre}{val}".format(nombre=i.get("nom", ""), val=valoracion)
        url = "{url}?id={id}".format(url=api_temp, id=i.get("id", ""))

        thumbnail = ""
        fanart = ""
        if i.get("posterurl", ""):
            thumbnail = "http://image.tmdb.org/t/p/w342{file}".format(file=i.get("posterurl", ""))
        if i.get("backurl", ""):
            fanart = "http://image.tmdb.org/t/p/w1280{file}".format(file=i.get("backurl", ""))

        plot = i.get("info", "")
        if plot is None:
            plot = ""

        itemlist.append(Item(channel=__channel__, action="episodios", title=title, url=url, server="torrent",
                             thumbnail=thumbnail, fanart=fanart, show=title, plot=plot, folder=True))

    if len(itemlist) == 50:
        url = re.sub(r'page=(\d+)', r'page=' + str(int(re.search('\d+', item.url).group()) + 1), item.url)
        itemlist.append(Item(channel=__channel__, action="series", title=">> Página siguiente", url=url))

    return itemlist


def episodios(item):
    logger.info("pelisalacarta.pelismagnet episodios")
    itemlist = []

    data = scrapertools.cachePage(item.url)
    data = jsontools.load_json(data)
    # logger.info("lista {0}".format(data))

    for i in data.get("temporadas", []):
        for j in i.get("capituls", []):

            numero = j.get("infocapitul", "")
            if not numero:
                numero = "{temp}x{cap}".format(temp=i.get("numerotemporada", ""), cap=j.get("numerocapitul", ""))

            titulo = j.get("nomcapitul", "")
            if not titulo:
                titulo = "Capítulo {num}".format(num=j.get("numerocapitul", ""))

            calidad = ""
            if j.get("links", {}).get("calitat", ""):
                calidad = " [{calidad}]".format(calidad=j.get("links", {}).get("calitat", ""))

            title = "{numero} {titulo}{calidad}".format(numero=numero, titulo=titulo, calidad=calidad)

            if j.get("links", {}).get("magnet", ""):
                url = j.get("links", {}).get("magnet", "")
            else:
                return [Item(channel=__channel__, title='No hay enlace magnet disponible para este capitulo')]

            plot = i.get("overviewcapitul", "")
            if plot is None:
                plot = ""

            itemlist.append(Item(channel=__channel__, action="play", title=title, url=url, server="torrent",
                                 fanart=item.fanart, thumbnail=item.thumbnail, plot=plot, folder=False))

    return itemlist


def pelis(item):
    logger.info("pelisalacarta.pelismagnet pelis")

    itemlist = []
    data = scrapertools.cachePage(item.url)
    lista = jsontools.load_json(data)

    for i in lista:

        punt = i.get("puntuacio", "")
        valoracion = ""

        if punt and not 0:
            valoracion = "  (Val: {punt})".format(punt=punt)

        if i.get("magnets", {}).get("M1080", {}).get("magnet", ""):
            url = i.get("magnets", {}).get("M1080", {}).get("magnet", "")
            calidad = "[{calidad}]".format(calidad=i.get("magnets", {}).get("M1080", {}).get("quality", ""))
        else:
            url = i.get("magnets", {}).get("M720", {}).get("magnet", "")
            calidad = "[{calidad}]".format(calidad=i.get("magnets", {}).get("M720", {}).get("quality", ""))

        if not url:
            return [Item(channel=__channel__, title='No hay enlace magnet disponible para esta pelicula')]

        title = "{nombre} {calidad}{val}".format(nombre=i.get("nom", ""), val=valoracion, calidad=calidad)

        thumbnail = ""
        fanart = ""
        if i.get("posterurl", ""):
            thumbnail = "http://image.tmdb.org/t/p/w342{file}".format(file=i.get("posterurl", ""))
        if i.get("backurl", ""):
            fanart = "http://image.tmdb.org/t/p/w1280{file}".format(file=i.get("backurl", ""))

        plot = i.get("info", "")
        if plot is None:
            plot = ""

        itemlist.append(Item(channel=__channel__, action="play", title=title, url=url, server="torrent",
                             thumbnail=thumbnail, plot=plot, fanart=fanart, folder=False))

    if len(itemlist) == 50:
        url = re.sub(r'page=(\d+)', r'page=' + str(int(re.search('\d+', item.url).group()) + 1), item.url)
        itemlist.append(Item(channel=__channel__, action="pelis", title=">> Página siguiente", url=url))

    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.pelismagnet search")

    item.url = item.url % texto.replace(' ', '%20')
    if "/seapi" in item.url:
        return series(item)
    else:
        return pelis(item)
