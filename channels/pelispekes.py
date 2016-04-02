# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para pelispekes
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "pelispekes"
__category__ = "F"
__type__ = "generic"
__title__ = "Pelis Pekes"
__language__ = "ES"

DEBUG = config.get_setting("debug")

def isGeneric():
    return True

def mainlist(item):
    logger.info("[pelispekes.py] mainlist")
    itemlist=[]

    if item.url=="":
        item.url = "http://www.pelispekes.com/"

    data = scrapertools.cachePage(item.url)
    '''
    <div class="poster-media-card">
    <a href="http://www.pelispekes.com/un-gallo-con-muchos-huevos/" title="Un gallo con muchos Huevos">
    <div class="poster">
    <div class="title">
    <span class="under-title">Animacion</span>
    </div>
    <span class="rating">
    <i class="glyphicon glyphicon-star"></i><span class="rating-number">6.2</span>
    </span>
    <div class="poster-image-container">
    <img width="300" height="428" src="http://image.tmdb.org/t/p/w185/cz3Kb6Xa1q0uCrsTIRDS7fYOZyw.jpg" title="Un gallo con muchos Huevos" alt="Un gallo con muchos Huevos"/>
    '''
    patron  = '<div class="poster-media-card"[^<]+'
    patron += '<a href="([^"]+)" title="([^"]+)"[^<]+'
    patron += '<div class="poster"[^<]+'
    patron += '<div class="title"[^<]+'
    patron += '<span[^<]+</span[^<]+'
    patron += '</div[^<]+'
    patron += '<span class="rating"[^<]+'
    patron += '<i[^<]+</i><span[^<]+</span[^<]+'
    patron += '</span[^<]+'
    patron += '<div class="poster-image-container"[^<]+'
    patron += '<img width="\d+" height="\d+" src="([^"]+)"'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        url = scrapedurl
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")
        itemlist.append( Item(channel=item.channel , action="findvideos"   , title=title , url=url , thumbnail=thumbnail, fanart=thumbnail, plot=plot , viewmode="movie", hasContentDetails="true", contentTitle=title, contentThumbnail=thumbnail))

    # Extrae la pagina siguiente
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right')
    if next_page_url!="":
        itemlist.append( Item(channel=item.channel , action="mainlist"   , title=">> Página siguiente" , url=next_page_url ))

    return itemlist

def findvideos(item):
    logger.info("pelisalacarta.channels.zpeliculas findvideos item="+item.tostring())

    '''
    <h2>Sinopsis</h2>
    <p>Para que todo salga bien en la prestigiosa Academia Werth, la pequeña y su madre se mudan a una casa nueva. La pequeña es muy seria y madura para su edad y planea estudiar durante las vacaciones siguiendo un estricto programa organizado por su madre; pero sus planes son perturbados por un vecino excéntrico y generoso. Él le enseña un mundo extraordinario en donde todo es posible. Un mundo en el que el Aviador se topó alguna vez con el misterioso Principito. Entonces comienza la aventura de la pequeña en el universo del Principito. Y así descubre nuevamente su infancia y comprenderá que sólo se ve bien con el corazón. Lo esencial es invisible a los ojos. Adaptación de la novela homónima de Antoine de Saint-Exupery.</p>
    <div
    '''

    # Descarga la página para obtener el argumento
    data = scrapertools.cachePage(item.url)
    data = data.replace("www.pelispekes.com/player/tune.php?nt=","netu.tv/watch_video.php?v=")

    item.plot = scrapertools.find_single_match(data,'<h2>Sinopsis</h2>(.*?)<div')
    item.plot = scrapertools.htmlclean(item.plot).strip()
    item.contentPlot = item.plot
    logger.info("pelisalacarta.channels.zpeliculas findvideos plot="+item.plot)

    return servertools.find_video_items(item=item,data=data)

# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    novedades_items = novedades(mainlist_items[0])
    bien = False
    for novedades_item in novedades_items:
        mirrors = servertools.find_video_items( item=novedades_item )
        if len(mirrors)>0:
            bien = True
            break

    return bien