# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re
import urlparse

from core import httptools
from core import logger
from core import scrapertools
from core.item import Item

YOUTUBE_API = '34MasdJ3094m2ladKlei23%3#34mf#$'


def mainlist(item):
    itemlist = []

    itemlist.append(item.clone(title="Buscar", action="search"))

    return itemlist


def search(item, texto):

    texto = texto.replace(" ", "+")
    item.url = YOUTUBE_API + texto
    item.fulltitle = texto
    return findvideos(item)


def findvideos(item):

    itemlist = []
    itemlist.append('<iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" allowfullscreen></iframe>')

    from core import servertools
    itemlist = servertools.find_video_items(data=",".join(itemlist))
    for videoitem in itemlist:
        videoitem.fulltitle = item.fulltitle
        videoitem.channel = item.channel
        videoitem.thumbnail = item.thumbnail

    return itemlist
