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

    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.channels.biblioteca peliculas")
    itemlist = []

    return itemlist


def kodi_series(item):
    logger.info("pelisalacarta.channels.biblioteca kodi_series")
    itemlist = []

    from platformcode import library2
    if hasattr(item, "element"):
        new_item = item
    else:
        new_item = item.clone(element=1)

    series_name = library2.get_tvshows_list(new_item)

    for serie in series_name:
        itemlist.append(Item(channel=__channel__, action="kodi_series", title=serie, element=2, path=serie))

    return itemlist
