# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canal (javus) por Hernan_Ar_c
# ------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys


from core import logger
from core import config
from core import scrapertools
from core.item import Item
from core import servertools

DEBUG = config.get_setting("debug")

host='http://javus.net/'

def isGeneric():
    return True

def mainlist(item):
    
    if item.url=="":
        item.url = host
    
    logger.info("pelisalacarta.channels.javus mainlist")
    itemlist = []
    data = scrapertools.cache_page(item.url)
    patron ='<a href="([^"]+)" title="([^"]+)" rel="nofollow" class="post-image post-image-left".*?\s*<div class="featured-thumbnail"><img width="203" height="150" src="([^"]+)" class="attachment-featured size-featured wp-post-image" alt="" title="" \/><\/div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
       url = scrapedurl
       title = scrapedtitle.decode('utf-8')
       thumbnail = scrapedthumbnail
       fanart = ''
        
       if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"])")
       itemlist.append( Item(channel= item.channel, action="findvideos" ,title=title , url=url, thumbnail=thumbnail, fanart=fanart ))
        
#Paginacion
    title=''
    siguiente = scrapertools.find_single_match(data,"<a rel='nofollow' href='([^']+)' class='inactive'>Next <")
    ultima = scrapertools.find_single_match(data,"<a rel='nofollow' class='inactive' href='([^']+)'>Last <")
    if siguiente != ultima:
       titlen = 'Pagina Siguiente >>> '
       fanart = ''
       itemlist.append(Item(channel = item.channel, action = "mainlist", title =titlen, url = siguiente, fanart = fanart))
    return itemlist

    
def search(item,texto):
    logger.info("metaserie.py search")
    texto = texto.replace(" ","+")
    item.url = item.url+texto

    if texto!='':
        return todas(item)
    else:
        return []    
                                 
        
