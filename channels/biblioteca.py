# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para biblioteca de pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

from core import config
from core import logger
from core.item import Item

try:
    from platformcode import library2 as library
except ImportError:
    library = None

__channel__ = "biblioteca"
DEBUG = True


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.biblioteca mainlist")

    itemlist = list()
    if library:
        itemlist.append(Item(channel=__channel__, action="peliculas", title="Películas"))
        itemlist.append(Item(channel=__channel__, action="series", title="Series"))
        itemlist.append(Item(channel=__channel__, action="series_xml", title="Series.xml"))
    else:
        itemlist.append(Item(channel=__channel__, action="", title="Modulo de biblioteca no disponible para [{0}]".
                             format(config.get_platform())))
    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.channels.biblioteca peliculas")

    return library.get_movies(item.clone(element=2, action="play_from_library"))


def series(item):
    logger.info("pelisalacarta.channels.biblioteca series")

    if hasattr(item, "element"):
        new_item = item.clone(action="play_from_library", url=item.url)
    else:
        new_item = item.clone(element=1)

    logger.info("new_item {}".format(new_item.tostring()))
    return library.get_tvshows(new_item)


def series_xml(item):
    logger.info("pelisalacarta.channels.biblioteca series_xml")

    # eliminar huerfanos
    return library.tvshows_file(item)
