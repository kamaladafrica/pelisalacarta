# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import re
import urlparse
import requests

from channels import filtertools
from core import config
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools
from channelselector import get_thumb
from channels import renumbertools
from core import tmdb

host = "https://serieslan.com"

def mainlist(item):
    logger.info()
    thumb_series = get_thumb("squares", "thumb_canales_series.png")


    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="lista", title="Series", url=host,thumbnail=thumb_series, page=0))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    return itemlist

def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" '
    patron += 'class="link">.+?<img src="([^"]+)".*?'
    patron += 'title="([^"]+)">'

    matches = scrapertools.find_multiple_matches(data, patron)
    
    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    max = min + num_items_x_pagina -1
    
    for link, img, name in matches[min:max]:
        title=name
        url=host+link
        scrapedthumbnail=host+img
        itemlist.append(item.clone(title=title, url=url, action="episodios", thumbnail=scrapedthumbnail, show=title, context=renumbertools.context))

    itemlist.append(Item(channel = item.channel,title="Página Siguiente >>", url = item.url, action="lista", page= item.page +1))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron_caps = '<li><span>Capitulo ([^"]+)\:<\/span><a href="([^"]+)">([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    data_info=scrapertools.find_single_match(data, '<div class="info">.+?<\/div><\/div>')
    patron_info='<img src="([^"]+)">.+?<\/span>([^"]+)<\/p><p><span>I.+?Reseña: <\/span>(.+?)<\/p><\/div>'
    scrapedthumbnail,show,scrapedplot = scrapertools.find_single_match(data,patron_info)
    scrapedthumbnail=host+scrapedthumbnail
    i=0
    epi=0
    for cap, link,name in matches:
        i=i+1
        season = 1
        episode = int(cap)
        season, episode = renumbertools.numbered_for_tratk(
            item.channel, item.show, season, episode)
        date=name
        title = "{0}x{1:02d} {2} ({3})".format(
            season, episode, "Episodio " + str(episode), date)
        url=host+"/"+link
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, show=show,plot=scrapedplot,thumbnail=scrapedthumbnail))

    if config.get_library_support() and len(itemlist) > 0:

        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la biblioteca de Kodi", url=item.url,

                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist

#def getUrlVideo(item):
def findvideos(item):
    ## Kodi 17+
    ## Openload as default server

    import base64

    itemlist = []

    ## Urls
    urlServer = "https://openload.co/embed/%s/"
    urlApiGetKey = "https://serieslan.com/idv.php?i=%s"

    ## JS
    def txc(key, str):
        s = range(256)
        j = 0
        res = ''
        for  i in range(256):
            j = (j + s[i] + ord(key[i % len(key)])) % 256
            x = s[i]
            s[i] = s[j]
            s[j] = x
        i = 0
        j = 0
        for y in range(len(str)):
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            x = s[i]
            s[i] = s[j]
            s[j] = x
            res += chr(ord(str[y]) ^ s[(s[i] + s[j]) % 256])
        return res

    data = httptools.downloadpage(item.url).data 
    logger.info("sassvxcv"+data)
    pattern = '<div id="video" idv="([^"]*)" ide="([^"]*)" ids="[^"]*" class="video">'
    idv, ide = scrapertools.find_single_match(data, pattern)
    thumbnail= scrapertools.find_single_match(data, '<div id="tab-1" class="tab-content current">.+?<img src="([^"]*)">')
    show= scrapertools.find_single_match(data, '<span>Episodio: <\/span>([^"]*)<\/p><p><span>Idioma')
    thumbnail=host+thumbnail
    data = httptools.downloadpage(urlApiGetKey % idv, headers={'Referer':item.url}).data
    video_url = urlServer % (txc(ide, base64.decodestring(data)))
    server="openload"
    itemlist.append(Item(channel=item.channel, action="play", title="Enlace encontrado en "+server, plot=show,show=show, url=video_url, thumbnail=thumbnail,server=server, folder=False))

    return itemlist

def play(item):
    logger.info()

    itemlist = []


    # Buscamos video por servidor ...

    devuelve = servertools.findvideosbyserver(item.url, item.server)

    if not devuelve:

        # ...sino lo encontramos buscamos en todos los servidores disponibles

        devuelve = servertools.findvideos(item.url, skip=True)


    if devuelve:

        # logger.debug(devuelve)
        itemlist.append(Item(channel=item.channel, title=item.contentTitle, action="play", server=devuelve[0][2],

                             url=devuelve[0][1],thumbnail=item.thumbnail, folder=False))


    return itemlist


