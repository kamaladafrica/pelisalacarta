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
    itemlist.append(Item(channel=__channel__, action="biblioteca", title="Biblioteca"))
    if config.get_library_support():
        itemlist.append(Item(channel=__channel__, action="mainlist", title="Kodi", folder=False))
        itemlist.append(Item(channel=__channel__, action="mainlist", title="      Películas", folder=False))
        itemlist.append(Item(channel=__channel__, action="kodi_series", title="      Series"))

    return itemlist


def kodi_series(item):
    logger.info("pelisalacarta.channels.biblioteca kodi_series")
    itemlist = []

    return itemlist
