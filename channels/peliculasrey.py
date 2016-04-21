# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculasrey
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core import jsontools
from core.item import Item
from servers import servertools

DEBUG = config.get_setting("debug")

__category__ = "A"
__type__ = "generic"
__title__ = "peliculasrey"
__channel__ = "peliculasrey"
__language__ = "ES"
__creationdate__ = "20160415"

def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.channels.peliculasrey mainlist")

    itemlist = []
    itemlist.append( Item(channel=__channel__, action="PorFecha" , title="Año de Lanzamiento", url="http://www.peliculasrey.com" ))
    itemlist.append( Item(channel=__channel__, action="Idiomas" , title="Idiomas"            , url="http://www.peliculasrey.com" ))
    itemlist.append( Item(channel=__channel__, action="calidades" , title="Por calidad"          , url="http://www.peliculasrey.com" ))
    itemlist.append( Item(channel=__channel__, action="generos" , title="Por género"          , url="http://www.peliculasrey.com" ))
    itemlist.append( Item(channel=__channel__, action="search"  , title="Buscar..."            , url="http://www.peliculasrey.com" ))
    
      
    return itemlist
    
def PorFecha(item):
    logger.info("pelisalacarta.channels.peliculasrey generos")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    data = scrapertools.find_single_match(data,'<section class="lanzamiento">(.*?)</section>')
    logger.info("data="+data)

    # Extrae las entradas (carpetas)
    patron  = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url,scrapedurl)
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="peliculas" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title))

    return itemlist

def Idiomas(item):
    logger.info("pelisalacarta.channels.peliculasrey generos")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    data = scrapertools.find_single_match(data,'<section class="idioma">(.*?)</section>')
    logger.info("data="+data)

    # Extrae las entradas (carpetas)
    patron  = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url,scrapedurl)
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="peliculas" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title))

    return itemlist

def calidades(item):
    logger.info("pelisalacarta.channels.peliculasrey generos")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    data = scrapertools.find_single_match(data,'<section class="calidades">(.*?)</section>')
    logger.info("data="+data)

    # Extrae las entradas (carpetas)
    patron  = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url,scrapedurl)
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="peliculas" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title))

    return itemlist

def generos(item):
    logger.info("pelisalacarta.channels.peliculasrey generos")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    data = scrapertools.find_single_match(data,'<section class="generos">(.*?)</section>')
    logger.info("data="+data)

    # Extrae las entradas (carpetas)
    patron  = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url,scrapedurl)
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="peliculas" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title))

    return itemlist


def search(item,texto):
    
    logger.info("pelisalacarta.channels.peliculasrey search")
    texto = texto.replace(" ","-")    
    item.url = "http://www.peliculasrey.com/?s=" + texto
    
    try:
        #return buscar(item)
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []
   

    
def peliculas(item):
    logger.info("pelisalacarta.channels.peliculasrey peliculas")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    logger.info("data="+data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    tabla_pelis= scrapertools.find_single_match(data, 'class="section col-17 col-main grid-125 overflow clearfix">(.*?)</div></section>')
    patron  = '<img src="([^"]+)" alt="([^"]+).*?href="([^"]+)'

    matches = re.compile(patron,re.DOTALL).findall(tabla_pelis)
    itemlist = []
    
    for scrapedthumbnail,scrapedtitle,scrapedurl in matches:
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot="", fulltitle=scrapedtitle, viewmode="movie"))

    next_page = scrapertools.find_single_match(data,'rel="next" href="([^"]+)')
    if next_page!="":
    #    itemlist.append( Item(channel=__channel__, action="peliculas" , title=">> Página siguiente" , url=item.url+next_page, folder=True))
        itemlist.append( Item(channel=__channel__, action="peliculas" , title=">> Página siguiente" , url=next_page, folder=True))
      
    return itemlist

def findvideos(item):
    logger.info("pelisalacarta.channels.peliculasrey findvideos")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    #logger.info("data="+data)

    # Extrae las entradas (carpetas)  
    patron  = 'hand" rel="([^"]+).*?title="(.*?)".*?<span>([^<]+)</span>.*?</span><span class="q">(.*?)<'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    
    for scrapedurl,nombre_servidor,idioma,calidad in matches:
        idioma = idioma.strip()
        calidad = calidad.strip()
        

        title = "Ver en "+nombre_servidor+" ("+idioma+") (Calidad "+calidad+")"
        url = scrapedurl
        thumbnail = ""
        plot = ""
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, folder=False))

    return itemlist


def play(item):
    logger.info("pelisalacarta.channels.peliculasrey play url="+item.url)

    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = __channel__

    return itemlist