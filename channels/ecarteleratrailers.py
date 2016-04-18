# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para trailers de ecartelera
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re
import urlparse

from core import config
from core import logger
from core import scrapertools
from core.item import Item

DEBUG = config.get_setting("debug")

__channel__ = "ecarteleratrailers"
__category__ = "F"
__type__ = "generic"
__title__ = "Trailers ecartelera"
__language__ = "ES,EN"

def isGeneric():
    return True

def mainlist(item):
    logger.info("[ecarteleratrailers.py] mainlist")
    itemlist=[]

    if item.url=="":
        item.url="http://www.ecartelera.com/videos/"
    
    # ------------------------------------------------------
    # Descarga la p�gina
    # ------------------------------------------------------
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # ------------------------------------------------------
    # Extrae las pel�culas
    # ------------------------------------------------------
    patron  = '<div class="cuadronoticia">.*?<img src="([^"]+)".*?'
    patron += '<div class="cnottxtv">.*?<h3><a href="([^"]+)">([^<]+)</a></h3>.*?'
    patron += '<img class="bandera" src="http\:\/\/www\.ecartelera\.com\/images\/([^"]+)"[^<]+'
    patron += '<br/>([^<]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[2] #unicode( , "iso-8859-1" , errors="replace" ).encode("utf-8")

        if match[3]=="fl_1.gif":
            scrapedtitle += " (Castellano)"
        elif match[3]=="fl_2.gif":
            scrapedtitle += " (Ingl�s)"
        
        scrapedurl = match[1]
        scrapedthumbnail = match[0]
        scrapedplot = match[4]

        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, server="directo", viewmode="movie_with_plot", folder=False))

    # ------------------------------------------------------
    # Extrae la p�gina siguiente
    # ------------------------------------------------------
    patron = '<a href="([^"]+)">Siguiente</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = "Pagina siguiente"
        scrapedurl = match
        scrapedthumbnail = ""
        scrapeddescription = ""

        # A�ade al listado de XBMC
        itemlist.append( Item(channel=__channel__, action="mainlist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, server="directo", folder=True))

    return itemlist

# Reproducir un v�deo
def play(item):
    logger.info("[ecarteleratrailers.py] play")
    itemlist=[]
    # Descarga la p�gina
    data = scrapertools.cachePage(item.url)
    logger.info(data)

    # Extrae las pel�culas
    patron  = "file\: '([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)

    if len(matches)>0:
        url = urlparse.urljoin(item.url,matches[0])
        logger.info("[ecarteleratrailers.py] url="+url)
        itemlist.append( Item(channel=__channel__, action="play" , title=item.title , url=url, thumbnail=item.thumbnail, plot=item.plot, server="directo", folder=False))

    return itemlist


# Verificaci�n autom�tica de canales: Esta funci�n debe devolver "True" si est� ok el canal.
def test():
    # mainlist
    mainlist_items = mainlist(Item())
    if len(mainlist_items)==0:
        print "ecartelera: Lista de canales vac�a"
        return False
    
    # Da por bueno el canal si alguno de los v�deos de "Novedades" devuelve mirrors
    video_items = play(mainlist_items[0])
    if len(mainlist_items)==0:
        print "ecartelera: No devuelve videos"
        return False

    return True