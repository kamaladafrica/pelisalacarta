# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canal (hentaienespanol) por Hernan_Ar_c
# ------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys


from core import logger
from core import config
from core import scrapertools
from core.item import Item
from core import servertools
#from core import httptools


DEBUG = config.get_setting("debug")

host='http://www.xn--hentaienespaol-1nb.net/'
headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
          ['Referer', host]]

def mainlist(item):
    logger.info("pelisalacarta.channels.hentaienespanol mainlist")

    itemlist = []
    

    itemlist.append( Item(channel=item.channel, title="Todos", action="todas", url=host,thumbnail='', fanart=''))
    
    itemlist.append( Item(channel=item.channel, title="Sin Censura", action="todas", url=host+'hentai/sin-censura/', thumbnail='', fanart=''))

    # itemlist.append( Item(channel=item.channel, title="Estrenos", action="todas", url=host+'category/estreno/', thumbnail='', fanart=''))
    
    # itemlist.append( Item(channel=item.channel, title="Categorias", action="categorias", url=host, thumbnail='', fanart=''))

   
    return itemlist

def todas(item):

    logger.info("pelisalacarta.channels.hentaienespanol todas")
    itemlist = []
    data = scrapertools.cache_page(item.url)
    logger.debug (data)
    patron ='<div class="box-peli" id="post-.*?">.<h2 class="title">.<a href="([^"]+)">([^<]+)<\/a>.*?'
    patron+='height="170px" src="([^"]+)'
           
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle, scrapedthumbnail in matches: 
        url = scrapedurl
        title = scrapedtitle#.decode('utf-8')
        thumbnail = scrapedthumbnail
        fanart = ''
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"])")
        itemlist.append( Item(channel=item.channel, action="findvideos" ,title=title , url=url, thumbnail=thumbnail, fanart=fanart ))
            
#Paginacion
    title=''
    siguiente = scrapertools.find_single_match(data,'class="nextpostslink" rel="next" href="([^"]+)">')
    title = 'Pagina Siguiente >>> '
    fanart = ''
    itemlist.append(Item(channel = item.channel, action = "todas", title =title, url = siguiente, fanart = fanart))
    return itemlist

    
def search(item,texto):
    logger.info("hentaienespanol.py search")
    texto = texto.replace(" ","+")
    item.url = item.url+texto

    if texto!='':
        return todas(item)
    else:
        return []
        
def findvideos(item):
    logger.info ('peliculasalacarta.channel.estadepelis findvideos')
    
    itemlist =[]

    data = scrapertools.cache_page(item.url)
    logger.debug(data)
    patron = '<li.*?<a href="([^"]+)" target="_blank"><i class="icon-metro online"><\/i><span>Ver.*?<\/span><\/a> <\/li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl in matches:
        title = item.title
        url =scrapedurl
        itemlist.append(item.clone(title=title, url=url, action="play"))

    return itemlist


def play(item):
     logger.info()
     itemlist = []
     item.url = item.url.replace(' ','%20')
     #data = scrapertools.find_single_match(item.url,'<iframe src="([^"]+)" scrolling="no" frameborder="0"')
     #data = httptools.downloadpage(item.url, headers = headers)
     data = scrapertools.anti_cloudflare(item.url, host=host, headers=headers)
     logger.debug(data)
     url = scrapertools.find_single_match(data,'<iframe.*?src="([^"]+)".*?frameborder="0"')
     itemlist = servertools.find_video_items(data=data)
     logger.debug(data)

     return itemlist  