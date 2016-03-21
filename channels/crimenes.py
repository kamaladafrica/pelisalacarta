# -*- coding: utf-8 -*-
import urlparse,urllib2,urllib,re
import os, sys, xbmc

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "crimenes"
__category__ = "D"
__type__ = "generic"
__title__ = "Crimenes"
__language__ = "ES"

DEBUG = config.get_setting("debug")
from unicodedata import normalize

def remover_acentos(txt):
    codif='utf-8'
    txt.replace('Ã','i')
    return txt

def isGeneric():
    return True

# Main list manual
def listav(item):

    itemlist=[]
    
    #data = scrapertools.cache_page(item.url).decode('iso-8859-1').encode('utf-8')                   
    data = scrapertools.cache_page(item.url)
    data = data.replace("\n","").replace("\t", "")
    data = scrapertools.decodeHtmlentities(data)
    
    

    patronbloque='<li><div class="yt-lockup.*?<img src="[^"]+" alt="" data-thumb="([^"]+)".*?<h3 class="yt-lockup-title "><a href="([^"]+)".*?title="([^"]+)".*?</h3>'	
    #patronbloque='<li><div class="yt-lockup.*?<img src="([^"]+)".*?<h3 class="yt-lockup-title "><a href="([^"]+)".*?title="([^"]+)".*?</h3>'	
    matchesbloque = re.compile(patronbloque,re.DOTALL).findall(data)    
    scrapertools.printMatches(matchesbloque)
    
    
    for scrapedthumbnail,scrapedurl,scrapedtitle in matchesbloque:
        scrapedtitle=remover_acentos(scrapedtitle)
        url = urlparse.urljoin(item.url,scrapedurl)               
        thumbnail=urlparse.urljoin(item.thumbnail,scrapedthumbnail)
        xbmc.log("$ "+scrapedurl+" "+scrapedtitle+" "+scrapedthumbnail)   
        itemlist.append( Item(channel=__channel__, action="play", title=scrapedtitle, fulltitle=scrapedtitle , url=url, thumbnail=thumbnail,fanart=thumbnail) )    
    
    
    #Paginacion 
    
    patronbloque='<div class="yt-uix-pager search-pager branded-page-box spf-link " role="navigation">(.*?)</div>'	
    matches = re.compile(patronbloque,re.DOTALL).findall(data)    
    for bloque in matches:              
        patronvideo='<a href="([^"]+)"'
        matchesx = re.compile(patronvideo,re.DOTALL).findall(bloque)            
        for scrapedurl in matchesx:          
            url = urlparse.urljoin(item.url,scrapedurl)                        
        # solo me quedo con el ultimo enlace
        itemlist.append( Item(channel=__channel__, action="listav", title="Siguiente pag >>", fulltitle="Siguiente Pag >>" , url=url, thumbnail=item.thumbnail,fanart=item.fanart) )     
   	   
    return itemlist

def mainlist(item):

    logger.info("[crimenes] mainlist")
    itemlist = []
    
    item.url='https://www.youtube.com/results?q=crimenes+imperfectos&sp=CAI%253D'
    scrapedtitle="[COLOR white]Crimenes [COLOR red]Imperfectos[/COLOR]"    
    item.thumbnail=urlparse.urljoin(item.thumbnail,"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQ2PcyvcYIg6acvdUZrHGFFk_E3mXK9QSh-5TypP8Rk6zQ6S1yb2g")
    item.fanart=urlparse.urljoin(item.fanart,"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQ2PcyvcYIg6acvdUZrHGFFk_E3mXK9QSh-5TypP8Rk6zQ6S1yb2g")
    
    itemlist.append( Item(channel=__channel__, action="listav", title=scrapedtitle, fulltitle=scrapedtitle , url=item.url, thumbnail=item.thumbnail, fanart=item.fanart) )    
    
    item.url='https://www.youtube.com/results?q=cuarto+milenio+%2Boficial&sp=CAI%253D'
    scrapedtitle="[COLOR green]Cuarto[/COLOR] [COLOR White]Milenio[/COLOR]"    
    item.thumbnail=urlparse.urljoin(item.thumbnail,"http://cuatrostatic-a.akamaihd.net/cuarto-milenio/Cuarto-Milenio-analiza-fantasma-Granada_MDSVID20100924_0063_3.jpg")
    item.fanart=urlparse.urljoin(item.fanart,"http://cuatrostatic-a.akamaihd.net/cuarto-milenio/programas/temporada-07/t07xp32/fantasma-universidad_MDSVID20120420_0001_3.jpg")
    
    itemlist.append( Item(channel=__channel__, action="listav", title=scrapedtitle, fulltitle=scrapedtitle , url=item.url, thumbnail=item.thumbnail, fanart=item.fanart) )    
    

    return itemlist
    
    
def play(item):
   logger.info("[crimenes] play url="+item.url)
   
   itemlist = servertools.find_video_items(data=item.url)
    
   return itemlist
