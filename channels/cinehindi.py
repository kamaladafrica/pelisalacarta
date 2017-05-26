# -*- coding: UTF-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------


import re
import urlparse

from core import config
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools

host = "http://www.cinehindi.com/"

def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="genero", title="Generos", url=host))
    itemlist.append(Item(channel=item.channel, action="lista", title="Novedades", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=urlparse.urljoin(host, "?s=")))
    return itemlist

def genero(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_generos='<ul id="menu-submenu" class=""><li id="menu-item-.+?"(.+)<\/li><\/ul>'
    data_generos = scrapertools.find_single_match(data, patron_generos)
    patron ='class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-.*?"><a href="(.*?)">(.*?)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data_generos, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action='lista', title=scrapedtitle, url=scrapedurl))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ","+")
    item.url = item.url+texto
    #logger.info("item="+item.url)
    if texto!='':
       return lista(item)

def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data) # Eliminamos tabuladores, dobles espacios saltos de linea, etc...
    patron = 'class="item">.*?' # Todos los items de peliculas (en esta web) empiezan con esto
    patron += '<a href="([^"]+).*?' # scrapedurl
    patron += '<img src="([^"]+).*?' # scrapedthumbnail
    patron += 'alt="([^"]+).*?' # scrapedtitle
    patron += '<span class="ttx">([^<]+).*?' # scrapedplot
    patron += '<div class="fixyear">(.*?)</span></div></div>' # scrapedfixyear


    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedplot, scrapedfixyear in matches:
        patron = '<span class="year">([^<]+)'  # scrapedyear
        scrapedyear = scrapertools.find_single_match(scrapedfixyear, patron)
        if scrapedyear:
            scrapedtitle += ' (%s)' % (scrapedyear)

        patron = '<span class="calidad2">([^<]+).*?'  # scrapedquality
        scrapedquality = scrapertools.find_single_match(scrapedfixyear,patron)
        if scrapedquality:
            scrapedtitle += ' [%s]'%(scrapedquality)

        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, plot=scrapedplot, action="findvideos", extra=scrapedtitle,
                                   show=scrapedtitle, thumbnail=scrapedthumbnail, contentType="movie", context=["buscar_trailer"]))

    #Paginacion
    patron_genero='<h1>([^"]+)<\/h1>'
    genero = scrapertools.find_single_match(data,patron_genero)
    if genero=="Romance" or genero=="Drama":
        patron  = "<a rel='nofollow' class=previouspostslink' href='([^']+)'>Siguiente "
    else:
        patron  = "<span class='current'>.+?href='(.+?)'>"

    next_page_url = scrapertools.find_single_match(data,patron)

    if next_page_url!="":
        item.url=next_page_url
        import inspect
        itemlist.append(Item(channel = item.channel,action = "lista",title = ">> Página siguiente", url = next_page_url, thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'))
    return itemlist



def findvideos(item):
    logger.info()

    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    itemlist.extend(servertools.find_video_items(data=data))
    patron_show='<div class="data"><h1 itemprop="name">([^<]+)<\/h1>'
    show = scrapertools.find_single_match(data,patron_show)
    for videoitem in itemlist:
        videoitem.channel=item.channel
    #itemlist.append(Item(channel=item.channel, title="Añadir película a la biblioteca", url=item.url, action="add_pelicula_to_library", extra="", show=show))
    if config.get_library_support() and len(itemlist) > 0 :
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la biblioteca[/COLOR]', url=item.url,
                             action="add_pelicula_to_library", extra="findvideos", contentTitle = show))

    return itemlist



