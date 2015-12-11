# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para xhamster
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# Por boludiko
#------------------------------------------------------------
import cookielib
import urlparse,urllib2,urllib,re
import os
import sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "xhamster"
__category__ = "X"
__type__ = "generic"
__title__ = "xHamster"
__language__ = "ES"
__adult__ = "true"

DEBUG = config.get_setting("debug")

def isGeneric():
    return True

def mainlist(item):
    logger.info("[xhamster.py] mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, action="videos"      , title="Útimos vídeos" , url="http://es.xhamster.com/"))
    itemlist.append( Item(channel=__channel__, action="categorias"    , title="Categorías"))
    itemlist.append( Item(channel=__channel__, action="votados"    , title="Más votados"))
    itemlist.append( Item(channel=__channel__, action="search"    , title="Buscar", url="http://xhamster.com/search.php?q=%s&qcat=video"))
    return itemlist

# REALMENTE PASA LA DIRECCION DE BUSQUEDA

def search(item,texto):
    logger.info("[xhamster.py] search")
    tecleado = texto.replace( " ", "+" )
    item.url = item.url % tecleado
    item.extra = "buscar"
    return videos(item)

# SECCION ENCARGADA DE BUSCAR

def videos(item):
    logger.info("[xhamster.py] videos")
    data = scrapertools.downloadpageGzip(item.url)
    itemlist = []

    if item.extra != "buscar":
        data = scrapertools.get_match(data,'<div class="boxC videoList clearfix">(.*?)<div id="footer">')
        patron = "<div class='vDate'>.*?<\/div><a href='([^']+)'.*?><img src='([^']+)'.*?><img.*?><b>([^']+)</b><u>([^']+)</u>"
        matches = re.compile(patron,re.DOTALL).findall(data)
        for scrapedurl,scrapedthumbnail,time,title in matches:
            scrapedtitle = "" + time + " - " + title
            # Depuracion
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")            
            itemlist.append( Item(channel=__channel__, action="detail" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, folder=True))
		
    patron = "<div class='video'><a href='([^']+)'.*?><img src='([^']+)'.*?><img.*?><b>([^']+)</b><u>([^']+)</u>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,time,title in matches:
        scrapedtitle = "" + time + " - " + title
        # Depuracion
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")            
        itemlist.append( Item(channel=__channel__, action="detail" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, folder=True))
        
    # # EXTRAE EL PAGINADOR
    if item.extra == "buscar":
        patron  = "<a href='([^']+)' class='last'"
    else:
        patron  = "<div class='pager'>.*?<span>.*?<a href='([^']+)'>([^']+)<\/a>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        if item.extra == "buscar":
            page = scrapertools.find_single_match(match, "page=(\d+)")
            scrapedurl = match.replace("amp;","&")
            itemlist.append( Item(channel=__channel__, action="videos", title= ">> Página " + page , url=scrapedurl , extra="buscar", folder=True) )
        else:
            page = match[1]
            scrapedurl = match[0]
            itemlist.append( Item(channel=__channel__, action="videos", title= ">> Página " + page , url=scrapedurl , folder=True) )

    return itemlist

# SECCION ENCARGADA DE VOLCAR EL LISTADO DE CATEGORIAS CON EL LINK CORRESPONDIENTE A CADA PAGINA
    
def categorias(item):
    logger.info("[xhamster.py] categorias")
    itemlist = []

    itemlist.append( Item(channel=__channel__, action="lista" , title="Heterosexual", url="http://es.xhamster.com/channels.php"))
    itemlist.append( Item(channel=__channel__, action="lista" , title="Transexuales"  , url="http://es.xhamster.com/channels.php"))
    itemlist.append( Item(channel=__channel__, action="lista" , title="Gays"  , url="http://es.xhamster.com/channels.php"))
    return itemlist

def votados(item):
    logger.info("[xhamster.py] categorias")
    itemlist = []

    itemlist.append( Item(channel=__channel__, action="videos" , title="Día", url="http://es.xhamster.com/rankings/daily-top-videos.html"))
    itemlist.append( Item(channel=__channel__, action="videos" , title="Semana"  , url="http://es.xhamster.com/rankings/weekly-top-videos.html"))
    itemlist.append( Item(channel=__channel__, action="videos" , title="Mes"  , url="http://es.xhamster.com/rankings/monthly-top-videos.html"))
    itemlist.append( Item(channel=__channel__, action="videos" , title="De siempre"  , url="http://es.xhamster.com/rankings/alltime-top-videos.html"))
    return itemlist

def lista(item):
    logger.info("[xhamster.py] lista")
    itemlist = []
    data = scrapertools.downloadpageGzip(item.url)
    #data = data.replace("\n","")
    #data = data.replace("\t","")

    if item.title == "Gays":
        data = scrapertools.get_match(data,'<div class="title">'+item.title+'</div>.*?<div class="list">(.*?)<div id="footer">')
    else:
        data = scrapertools.get_match(data,'<div class="title">'+item.title+'</div>.*?<div class="list">(.*?)<div class="catName">')
    patron = '(<div.*?</div>)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        data = data.replace(match, "")
    patron = 'href="([^"]+)">(.*?)</a>'
    data = ' '.join(data.split())
    logger.info(data)
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append( Item(channel=__channel__, action="videos", title=scrapedtitle, url=scrapedurl, folder=True) )
    
    sorted_itemlist = sorted(itemlist, key=lambda Item: Item.title)
    return sorted_itemlist

# OBTIENE LOS ENLACES SEGUN LOS PATRONES DEL VIDEO Y LOS UNE CON EL SERVIDOR
def detail(item):
    logger.info("[xhamster.py] play")
    itemlist = []

    data = scrapertools.cachePage(item.url)
    logger.debug(data)

    patron = 'sources: {"240p":"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        url = url.replace("\\", "")
        logger.debug("url="+url)
        itemlist.append( Item(channel=__channel__, action="play" , title=item.title + " 240p", fulltitle=item.fulltitle , url=url, thumbnail=item.thumbnail, server="directo", folder=False))
		
    patron = 'sources:.*?"480p":"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
		for url in matches:
			url = url.replace("\\", "")
			logger.debug("url="+url)
			itemlist.append( Item(channel=__channel__, action="play" , title=item.title + " 480p", fulltitle=item.fulltitle , url=url, thumbnail=item.thumbnail, server="directo", folder=False))

    patron = 'sources:.*?"720p":"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
		for url in matches:
			url = url.replace("\\", "")
			logger.debug("url="+url)
			itemlist.append( Item(channel=__channel__, action="play" , title=item.title + " 720p", fulltitle=item.fulltitle , url=url, thumbnail=item.thumbnail, server="directo", folder=False))
    return itemlist


# Verificación automática de canales: Esta función debe devolver "True" si todo está ok en el canal.
def test():
    bien = True

    # mainlist
    mainlist_itemlist = mainlist(Item())
    video_itemlist = videos(mainlist_itemlist[0])
    
    # Si algún video es reproducible, el canal funciona
    for video_item in video_itemlist:
        play_itemlist = play(video_item)

        if len(play_itemlist)>0:
            return True

    return False