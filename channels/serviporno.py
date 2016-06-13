# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para serviporno
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re
import sys
import urlparse

from core import config
from core import logger
from core import scrapertools
from core.item import Item

DEBUG = config.get_setting("debug")

def isGeneric():
    return True

def mainlist(item):
    logger.info("[serviporno.py] mainlist")
    itemlist = []
    itemlist.append( Item(channel=item.channel, action="videos"      , title="Útimos videos" , url="http://www.serviporno.com/"))
    itemlist.append( Item(channel=item.channel, action="videos"      , title="Más vistos"    , url="http://www.serviporno.com/mas-vistos/"))
    itemlist.append( Item(channel=item.channel, action="videos"      , title="Más votados"   , url="http://www.serviporno.com/mas-votados/"))
    itemlist.append( Item(channel=item.channel, action="categorias"  , title="Categorias"    , url="http://www.serviporno.com/categorias/"))
    itemlist.append( Item(channel=item.channel, action="chicas"      , title="Chicas"        , url="http://www.serviporno.com/pornstars/"))
    itemlist.append( Item(channel=item.channel, action="search"      , title="Buscar"        , url="http://www.serviporno.com/search/?q="))
    return itemlist

def search(item,texto):
    logger.info("[serviporno.py] search")
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []
        
def videos(item):
    logger.info("[serviporno.py] videos")
    itemlist = []
    data = scrapertools.downloadpage(item.url)

    patron  = '<div class="wrap-box-escena">.*?'
    patron += '<div class="box-escena">.*?'
    patron += '<a href="([^"]+)" data-stats-video-id="[^"]+" data-stats-video-name="([^"]+)" data-stats-video-category="[^"]*" data-stats-list-name="[^"]*" data-stats-list-pos="[^"]*">.*?'
    patron += '<img src="([^"]+)" data-src="[^"]+" alt="[^"]+" id=\'[^\']+\' class="thumbs-changer" data-thumbs-prefix="[^"]+" height="150px" width="175px" border=0 />'
    
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    logger.info(str(matches))
    for url,title, thumbnail  in matches:
        url = urlparse.urljoin(item.url , url)          
        itemlist.append( Item(channel=item.channel, action='play', title=title , url=url , thumbnail=thumbnail) )
        
    #Paginador
    patron = '<a href="([^<]+)">Siguiente &raquo;</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)  
    if len(matches) >0:
      url = "http://www.serviporno.com"+matches[0]
      itemlist.append( Item(channel=item.channel, action="videos", title="Página Siguiente" , url=url , thumbnail="" , folder=True) )
      
    return itemlist

def chicas(item):
    logger.info("[serviporno.py] chicas")
    itemlist = []
    data = scrapertools.downloadpage(item.url)
    
    patron ='<div class="box-chica">.*?'
    patron +='<a href="([^"]+)" title="">.*?'
    patron +='<img class="img" src=\'([^"]+)\' width="175" height="150" border=\'0\' alt="[^"]+"/>.*?'
    patron +='</a>[^<]{1}<h4><a href="[^"]+" title="">([^"]+)</a></h4>.*?'
    patron +='<a class="total-videos" href="[^"]+" title="">([^<]+)</a>'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,thumbnail, title, videos  in matches:
        url = urlparse.urljoin( "http://www.serviporno.com" , url )
        title = title +" ("+videos+")"
        itemlist.append( Item(channel=item.channel, action='videos', title=title , url=url , thumbnail=thumbnail , plot="") )
    return itemlist

    
def categorias(item):
    logger.info("[serviporno.py] categorias")
    itemlist = []
    data = scrapertools.downloadpage(item.url)

    patron  = '<div class="wrap-box-escena">.*?'
    patron += '<div class="cat box-escena">.*?'
    patron += '<a href="([^"]+)"><img src="([^"]+)" alt="Webcam" height="150" width="175" border=0 /></a>.*?'
    patron += '<h4><a href="[^"]+">([^<]+)</a></h4>'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,thumbnail, title  in matches:
        url = urlparse.urljoin(item.url , url)
        itemlist.append( Item(channel=item.channel, action='videos', title=title , url=url , thumbnail=thumbnail , plot="") )
    return itemlist

def play(item):
    logger.info("[serviporno.py] play")
    itemlist=[]
    data = scrapertools.downloadpage(item.url)
    url= scrapertools.get_match(data,"url: '([^']+)',\s*framesURL:" )
    itemlist.append( Item(channel=item.channel, action="play", server="directo", title=item.title , url=url , thumbnail=item.thumbnail , plot=item.plot , folder=False) )

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