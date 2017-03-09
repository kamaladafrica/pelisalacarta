# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re

from core import httptools
from core import logger
from core import scrapertools
from core.item import Item

HOST = "http://documentales-online.com/"


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Novedades", action="listado", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Categorías", action="categorias", url=HOST))

    return itemlist


def listado(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    logger.debug("datito %s" % data)
    pagination = scrapertools.find_single_match(data, '<div class="older"><a href="([^"]+)"')
    if not pagination:
        pagination = scrapertools.find_single_match(data, '<span class=\'current\'>\d</span>'
                                                          '<a class="page larger" href="([^"]+)">')

    patron = '<ul class="sp-grid">(.*?)</ul>'
    data = scrapertools.find_single_match(data, patron)

    matches = re.compile('<a href="([^"]+)">(.*?)</a>', re.DOTALL).findall(data)

    for url, title in matches:
        itemlist.append(item.clone(title=title, url=url, action="findvideos", fulltitle=title))

    if pagination:
        itemlist.append(item.clone(title=">> Página siguiente", url=pagination))

    return itemlist


def categorias(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)

    data = scrapertools.find_single_match(data, 'a href="#">Categorías</a><ul class="sub-menu">(.*?)</ul>')

    logger.debug("datito %s" % data)

    matches = re.compile('<a href="([^"]+)">(.*?)</a>', re.DOTALL).findall(data)

    for url, title in matches:
        itemlist.append(item.clone(title=title, url=url, action="listado", fulltitle=title))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)

    data = scrapertools.find_single_match(data, 'src="(https://www\.youtube\.com/[^?]+)')

    from core import servertools
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        videoitem.fulltitle = item.fulltitle
        videoitem.channel = item.channel
        # videoitem.thumbnail = item.thumbnail

    return itemlist
