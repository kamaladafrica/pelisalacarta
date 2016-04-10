# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para biblioteca de pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

from core import config
from core import logger
from core.item import Item

__channel__ = "biblioteca"
DEBUG = True


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.biblioteca mainlist")
   
    itemlist = list()
    itemlist.append(Item(channel=__channel__, action="peliculas", title="Películas"))
    itemlist.append(Item(channel=__channel__, action="series", title="Series"))
    if config.get_library_support():
        itemlist.append(Item(channel=__channel__, action="mainlist", title=""))
        plot = "contenido agregado a la biblioteca de Kodi"
        itemlist.append(Item(channel=__channel__, action="mainlist", title="Kodi", plot=plot))
        itemlist.append(Item(channel=__channel__, action="kodi_pelis", title="      Películas"))
        itemlist.append(Item(channel=__channel__, action="kodi_series", title="      Series"))
        itemlist.append(Item(channel=__channel__, action="mainlist", title=""))
        itemlist.append(Item(channel=__channel__, action="series_xml", title="      Series.xml"))

    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    itemlist = []

    return itemlist


def kodi_pelis(item):
    logger.info("pelisalacarta.channels.biblioteca kodi_pelis")

    from platformcode import library2

    return library2.get_movies(item.clone(element=2, action="mainlist"))


def kodi_series(item):
    logger.info("pelisalacarta.channels.biblioteca kodi_series")

    from platformcode import library2
    if hasattr(item, "element"):
        new_item = item.clone(action="play_from_library", url=item.url)
    else:
        new_item = item.clone(element=1)

    return library2.get_tvshows(new_item)


def series_xml(item):
    logger.info("pelisalacarta.channels.biblioteca kodi_series")

    # eliminar huerfanos
    from platformcode import library2

    return library2.tvshows_file(item)
