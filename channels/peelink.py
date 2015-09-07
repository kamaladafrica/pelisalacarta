# -*- coding: utf-8 -*-
#-----------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peelink - Por Kampanita-2015 
# ( con ayuda de neno1978, DrZ3r0, y robalo )
# 7/9/2015
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#-----------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "peelink"
__category__ = "F,L"
__type__ = "generic"
__title__ = "Peelink"
__language__ = "ES"

DEBUG = config.get_setting("debug")

def isGeneric():
    return True

# Main list manual

def mainlist(item):
    logger.info("[peelink] mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, action="menupelis", title="Peliculas",  url="http://www.peelink2.org" , thumbnail="http://primerasnoticias.com/wp-content/uploads/2012/07/game1.jpg", fanart="http://primerasnoticias.com/wp-content/uploads/2012/07/game1.jpg") )
    itemlist.append( Item(channel=__channel__, action="porcat", title="Por Categoria",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQDsZyDowjAAE23njJbp9hYZRe9viAuq-f1niz2nRC4jNwXkD6W", fanart="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQDsZyDowjAAE23njJbp9hYZRe9viAuq-f1niz2nRC4jNwXkD6W") )
    itemlist.append( Item(channel=__channel__, action="search", title="Buscar...", url="http://www.peelink2.org/search/?s=", thumbnail="http://thumbs.dreamstime.com/x/buscar-pistas-13159747.jpg", fanart="http://thumbs.dreamstime.com/x/buscar-pistas-13159747.jpg"))
    return itemlist
    
def porcat(item):
    logger.info("[peelink] porcat")
    itemlist = []
   
    item.url = "http://www.peelink2.org/p/indice-de-pelis.html"
    
    itemlist.append( Item(channel=__channel__, action="menucat", title="Accion",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="http://primerasnoticias.com/wp-content/uploads/2012/07/game1.jpg", fanart="http://primerasnoticias.com/wp-content/uploads/2012/07/game1.jpg") )
    itemlist.append( Item(channel=__channel__, action="menucat", title="Anime",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQDsZyDowjAAE23njJbp9hYZRe9viAuq-f1niz2nRC4jNwXkD6W", fanart="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQDsZyDowjAAE23njJbp9hYZRe9viAuq-f1niz2nRC4jNwXkD6W") )
    itemlist.append( Item(channel=__channel__, action="menucat", title="Ciencia Ficción",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="http://st-listas.20minutos.es/images/2014-11/389838/list_640px.jpg?1416583998", fanart="http://st-listas.20minutos.es/images/2014-11/389838/list_640px.jpg?1416583998") )
    itemlist.append( Item(channel=__channel__, action="menucat", title="Comedia",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQlWwCJco1oc0Jlc5Jr6i1CcKoLWtZsEkFabDuuv4bFANk90LiE", fanart="https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQlWwCJco1oc0Jlc5Jr6i1CcKoLWtZsEkFabDuuv4bFANk90LiE") )
    itemlist.append( Item(channel=__channel__, action="menucat", title="Drama",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="http://upload.wikimedia.org/wikipedia/en/e/e2/Yes_stars_drama_logo.png", fanart="http://upload.wikimedia.org/wikipedia/en/e/e2/Yes_stars_drama_logo.png") )
    itemlist.append( Item(channel=__channel__, action="menucat", title="Infantil",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="http://bebefeliz.com/files/2013/05/pocoyo.jpg", fanart="http://bebefeliz.com/files/2013/05/pocoyo.jpg") )
    itemlist.append( Item(channel=__channel__, action="menucat", title="Terror",  url="http://www.peelink2.org/p/indice-de-pelis.html" , thumbnail="http://st-listas.20minutos.es/images/2013-05/362124/4039926_640px.jpg?1374169785", fanart="http://st-listas.20minutos.es/images/2013-05/362124/4039926_640px.jpg?1374169785") )            
    

    return itemlist

def menupelis(item):
    logger.info("[peelink] menupelis")
    itemlist = []
   
    item.url = "http://www.peelink2.org"

    data = scrapertools.cache_page(item.url).decode('iso-8859-1').encode('utf-8')          

    patronbloque='<p><a href=.*?>(.*?)</p>'
    matchesbloque = re.compile(patronbloque,re.DOTALL).findall(data)    
    scrapertools.printMatches(matchesbloque)
    
    for datos in matchesbloque:
        patron= '<a href="([^"]+)">.*?<img.*?src="([^"]+)".*?alt="([^"]+)".*?</a>'
        matches = re.compile(patron,re.DOTALL).findall(datos)    
        scrapertools.printMatches(matches)
    
        for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
            title = scrapedtitle.replace("Ver","")              
            title = title.replace("ver","")              
            url = urlparse.urljoin(item.url,scrapedurl)   
            thumbnail=urlparse.urljoin(item.thumbnail,scrapedthumbnail)   
            logger.info("[peelink]  title: " + title + " url: " + url )         
            itemlist.append( Item(channel=__channel__, action="verpeli", title=title, fulltitle=title , url=url, thumbnail=thumbnail) )
        
        
    try:
        next_page = scrapertools.get_match(data,'<span style="font-size: small;">\d+ DE \d+</span>.*?<a href="[^"]+".*?<a href="([^"]+)"')            
        title= "[COLOR red][B]Pagina siguiente »[/B][/COLOR]"
        itemlist.append( Item(channel=__channel__, title=title, url=next_page, action="menupelis",  folder=True) )
    except: pass
    
    
    logger.info("######################### "+next_page)        
    return itemlist 		
    
    
def menucat(item):
   
    logger.info("[peelink] menupecat")
    logger.info("[peelink] "+item.url)
    
    itemlist = []
       
    data = scrapertools.cache_page(item.url).decode('iso-8859-1').encode('utf-8')      
    
    patronenlaces= '<p><a href="http://www.peelink2.org/genero/.*?>'+item.title+'</a></p>(.*?)</ol>'

    matchesenlaces = re.compile(patronenlaces,re.DOTALL).findall(data)
   
    for bloque_enlaces in matchesenlaces:
    
        patron = '<a href="([^"]+)">(.*?)</a>'
        matches = re.compile(patron,re.DOTALL).findall(bloque_enlaces)
        scrapertools.printMatches(matches)
        for scrapedurl,scrapedtitle in matches:
            title = scrapedtitle.replace("Ver","")              
            title = title.replace("ver","")              
            url = urlparse.urljoin(item.url,scrapedurl)   
            logger.info("[peelink]  title: " + title + " url: " + url )         
            itemlist.append( Item(channel=__channel__, action="verpeli", title=title, fulltitle=title , url=url) )
        
        
        try:
            next_page = scrapertools.get_match(data,'<span style="font-size: small;">\d+ DE \d+</span>.*?<a href="[^"]+".*?<a href="([^"]+)"')            
            title= "[COLOR red][B]Pagina siguiente »[/B][/COLOR]"
            itemlist.append( Item(channel=__channel__, title=title, url=next_page, action="menupelis",  folder=True) )
        except: pass
        
        return itemlist
        
def verpeli(item):   
   
   logger.info("[peelink] verpeli")
   logger.info("[peelink] "+item.url)
    
   itemlist = []
            
   data = scrapertools.cache_page(item.url).decode('iso-8859-1').encode('utf-8')
    
   patronenlaces='<img class="alignnone.*?src="([^"]+)".*?</a>(.*?)</iframe>.*?</span></div>'
   matches = re.compile(patronenlaces,re.DOTALL).findall(data)    
   scrapertools.printMatches(matches)
   itemlist = []      
   for scrapedthumbnail,scrapedplot in matches:
       thumbnail=urlparse.urljoin(item.url,scrapedthumbnail)   
       plot=scrapertools.htmlclean(scrapedplot)
   #estos son los datos para plot 
   
   patron='<img class="alignnone.*?>(.*?)</span></div>'
   matches = re.compile(patron,re.DOTALL).findall(data)            
   scrapertools.printMatches(matches)
   
   for datos in matches:
       patron='<iframe src="([^"]+)".*?'
       match = re.compile(patron,re.DOTALL).findall(datos)            
       scrapertools.printMatches(match)
       for scrapedurl in match:
           url = urlparse.urljoin(item.url,scrapedurl)            
           surl = "[ [COLOR red]"+scrapertools.get_match(url,'.*?://(.*?)/')+"[/COLOR] ]" 
           itemlist.append( Item(channel=__channel__, action="play", fanart=thumbnail, thumbnail=thumbnail,title=item.title+" "+surl, fulltitle=item.title , url=url, plot=plot) )
   
   return itemlist
   

def play(item):
   logger.info("[peelink] play url="+item.url)
   
   itemlist = servertools.find_video_items(data=item.url)
    
   return itemlist
   

def search(item, texto):

   logger.info("[peelink] "+item.url)
   item.url = 'http://www.peelink2.org/?s=%s' % (texto)
   item.url = item.url+'#.Ve16eSXtlHw'
   logger.info("[peelink] "+item.url)
   
   data = scrapertools.cache_page(item.url).decode('iso-8859-1').encode('utf-8')
   
   patron = '<div class="contenti">.*?<a href="([^"]+)">'
   matches = re.compile(patron,re.DOTALL).findall(data)    
   scrapertools.printMatches(matches)
   itemlist = []
   
   for scrapedurl in matches:      
      patron='/ver-(.*?).html'
      title=scrapertools.get_match(scrapedurl,patron)      
      title=title.replace("-"," ")
      url = urlparse.urljoin(item.url,scrapedurl)      
      logger.info("[peelink] "+url)
      itemlist.append( Item(channel=__channel__, action="verpeli", title=title, fulltitle=title , url=url ) )
    
   return itemlist  
   
