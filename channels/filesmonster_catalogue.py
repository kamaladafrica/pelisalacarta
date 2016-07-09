# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para filesmonster.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re

from core import config
from core import logger
from core import scrapertools
from core.item import Item

DEBUG = config.get_setting("debug")

def strip_tags(value):
    return re.sub(r'<[^>]*?>', '', value)
    

def mainlist(item):
    logger.info("[filesmonster_catalogue.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=item.channel, action="unusualporn" , title="Canal unusualporn.net"         , thumbnail="http://filesmonster.biz/img/logo.png"))    
    itemlist.append( Item(channel=item.channel, action="filesmonster", title="Canal filesmonster.filesdl.net", thumbnail="http://filesmonster.biz/img/logo.png"))    
    return itemlist


def filesmonster(item):
    logger.info("[filesmonster_catalogue.py] filesmonster")

    itemlist = []
    itemlist.append( Item(channel=item.channel, action="videos"    , title="Ultimos vídeos" , thumbnail="http://photosex.biz/imager/w_400/h_400/9f869c6cb63e12f61b58ffac2da822c9.jpg", url="http://filesmonster.filesdl.net"))         
    itemlist.append( Item(channel=item.channel, action="categorias", title="Categorias"               , thumbnail="http://photosex.biz/imager/w_400/h_500/e48337cd95bbb6c2c372ffa6e71441ac.jpg", url="http://filesmonster.filesdl.net"))   
    itemlist.append( Item(channel=item.channel, action="search", title="Buscar en filesmonster.fliesdl.net"               , url="http://filesmonster.filesdl.net/posts/search?q=%s")) 
    return itemlist


def unusualporn(item):
    logger.info("[filesmonster_catalogue.py] unusualporn")

    itemlist = []
    itemlist.append( Item(channel=item.channel, action="videos_2", title="Últimos vídeos", url="http://unusualporn.net/", thumbnail="http://photosex.biz/imager/w_400/h_500/e48337cd95bbb6c2c372ffa6e71441ac.jpg"))    
    itemlist.append( Item(channel=item.channel, action="categorias_2", title="Categorías", url="http://unusualporn.net/", thumbnail="http://photosex.biz/imager/w_400/h_500/e48337cd95bbb6c2c372ffa6e71441ac.jpg"))   
    itemlist.append( Item(channel=item.channel, action="search", title="Buscar en unusualporn"               , url="http://unusualporn.net/search/%s"))  
    return itemlist

def categorias(item):
    logger.info("[filesmonster_catalogue.py] categorias")
    itemlist = [] 

    data = scrapertools.downloadpage(item.url)
    data = scrapertools.find_single_match(data,'Categories <b class="caret"></b></a>(.*?)RSS <b class="caret"></b></a>')
    
    patronvideos ='<a href="([^"]+)">([^<]+)</a>'
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for url, title in matches:
      itemlist.append( Item(channel=item.channel, action="videos", title=title , url=url)) 

    return itemlist



def categorias_2(item):
    logger.info("[filesmonster_catalogue.py] categorias")
    itemlist = [] 

    data = scrapertools.downloadpage(item.url)
  
    patronvideos ='<li class="cat-item cat-item-[\d]+"><a href="([^"]+)" title="[^"]+">([^<]+)</a><a class="rss_s" title="[^"]+" target="_blank" href="[^"]+"></a></li>'
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for url, title in matches:
      itemlist.append( Item(channel=item.channel, action="videos_2", title=title , url=url)) 

    return itemlist
    
    
    
def search(item,texto):
    logger.info("[filesmonster_catalogue.py] search:" + texto)
    original=item.url
    item.url = item.url % texto
    try:
        if original=='http://filesmonster.filesdl.net/posts/search?q=%s':
        	return videos(item)
        if original=='http://unusualporn.net/search/%s':
        	return videos_2(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []




def videos(item):
    logger.info("[filesmonster_catalogue.py] list")
    itemlist = []
    
    url = item.url
    while url and len(itemlist) < 25:
      data= scrapertools.downloadpage(url)
      patronvideos='<div class="panel-heading">.*?<a href="([^"]+)">([^<]+).*?</a>.*?<div class="panel-body" style="text-align: center;">.*?<img src="([^"]+)".*?'
      matches = re.compile(patronvideos,re.DOTALL).findall(data)

      for url, title, thumbnail in matches:
          title = title.strip()
          itemlist.append( Item(channel=item.channel, action="detail", title=title, fulltitle = title , url=url , thumbnail=thumbnail) )  
          
      url =  scrapertools.find_single_match(data, '<li><a href="([^"]+)">Next</a></li>').replace("&amp;","&")

    #Enlace para la siguiente pagina  
    if url:
      itemlist.append( Item(channel=item.channel, action="videos", title=">> Página Siguiente", url=url) )

    return itemlist


def videos_2(item):
    logger.info("[filesmonster_catalogue.py] list")
    itemlist = []
    
    url = item.url
    while url and len(itemlist) < 25:
      data= scrapertools.downloadpage(url)
      patronvideos ='data-link="([^"]+)" data-title="([^"]+)" src="([^"]+)" border="0" />';
      matches = re.compile(patronvideos,re.DOTALL).findall(data)

      for url, title, thumbnail in matches:
          itemlist.append( Item(channel=item.channel, action="detail_2", title=title, fulltitle = title , url=url, thumbnail=thumbnail)) 

      url =  scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace("&amp;","&")

    #Enlace para la siguiente pagina  
    if url:
      itemlist.append( Item(channel=item.channel, action="videos_2", title=">> Página Siguiente", url=url) )

    return itemlist
    



def detail(item):
    logger.info("[filesmonster_catalogue.py] detail")
    itemlist = []

    data=scrapertools.downloadpage(item.url)
    patronvideos  = '["|\'](http\://filesmonster.com/download.php\?[^"\']+)["|\']'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for url in matches:
        title = "Archivo %d: %s [filesmonster]" %(len(itemlist)+1, item.fulltitle)
        itemlist.append( Item(channel=item.channel , action="play" ,  server="filesmonster", title=title, fulltitle= item.fulltitle ,url=url, thumbnail=item.thumbnail, folder=False))



    patronvideos  = '["|\'](http\://filesmonster.com/folders.php\?[^"\']+)["|\']'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    for url in matches: 
      if not url == item.url:
        logger.info(url)
        logger.info(item.url)
        title = "Carpeta %d: %s [filesmonster]" %(len(itemlist)+1, item.fulltitle)
        itemlist.append( Item(channel=item.channel , action="detail" ,  title=title, fulltitle= item.fulltitle ,url=url, thumbnail=item.thumbnail, folder=True))


    return itemlist




def detail_2(item):
    logger.info("[filesmonster_catalogue.py] detail")
    itemlist = []

	 # descarga la pagina
    data=scrapertools.downloadpageGzip(item.url)
    data=data.split('<span class="filesmonsterdlbutton">Download from Filesmonster</span>')
    data=data[0]
    # descubre la url
    patronvideos  = 'href="http://filesmonster.com/download.php(.*?)".(.*?)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)    
    for match2 in matches:
    	url ="http://filesmonster.com/download.php"+match2[0] 
        title = "Archivo %d: %s [filesmonster]" %(len(itemlist)+1, item.fulltitle)
        itemlist.append( Item(channel=item.channel , action="play" ,  server="filesmonster", title=title, fulltitle= item.fulltitle ,url=url, thumbnail=item.thumbnail, folder=False))



    patronvideos  = '["|\'](http\://filesmonster.com/folders.php\?[^"\']+)["|\']'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    for url in matches: 
      if not url == item.url:
        logger.info(url)
        logger.info(item.url)
        title = "Carpeta %d: %s [filesmonster]" %(len(itemlist)+1, item.fulltitle)
        itemlist.append( Item(channel=item.channel , action="detail" ,  title=title, fulltitle= item.fulltitle ,url=url, thumbnail=item.thumbnail, folder=True))


    return itemlist
