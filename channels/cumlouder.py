# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canal para pelisalacarta by EpNiebla
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import logger
from core import scrapertools
from core.item import Item


def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone(title = "Últimos videos", action = "videos"        , url = "http://www.cumlouder.com/"))
    itemlist.append(item.clone(title = "Categorias"    , action = "categorias"    , url = "http://www.cumlouder.com/categories/"))
    itemlist.append(item.clone(title = "Pornstars"     , action = "pornstars_list", url = "http://www.cumlouder.com/girls/"))
    itemlist.append(item.clone(title = "Buscar"        , action = "search"        , url = "http://www.cumlouder.com/search?q=%s"))

    return itemlist

def search(item, texto):
  logger.info()

  item.url = item.url % texto
  item.action = "videos"
  try:
    return videos(item)
  except:
    import traceback
    logger.error(traceback.format_exc())
    return []

def pornstars_list(item):
  logger.info()
  itemlist = []
  for letra in "abcdefghijklmnopqrstuvwxyz":
    itemlist.append(item.clone(title=letra.upper(), url=urlparse.urljoin(item.url,letra), action ="pornstars"))

  return itemlist
  
def pornstars(item):
  logger.info()
  itemlist = []
  
  data = httptools.downloadpage(item.url).data
  patron  = '<a girl-url="[^"]+" class="[^"]+" href="([^"]+)" title="([^"]+)">[^<]+'
  patron += '<img class="thumb" src="([^"]+)" [^<]+<h2[^<]+<span[^<]+</span[^<]+</h2[^<]+'
  patron += '<span[^<]+<span[^<]+<span[^<]+</span>([^<]+)</span>'

  matches = re.compile(patron, re.DOTALL).findall(data)
  for url, title, thumbnail, count in matches:
    itemlist.append(item.clone(title="%s (%s videos)" % (title, count), url=urlparse.urljoin(item.url,url), action ="videos", thumbnail = thumbnail))
  
  #Paginador
  matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
  if matches:
    itemlist.append(item.clone(title="Pagina Siguiente", url=urlparse.urljoin(item.url,matches[0])))
  
  return itemlist 
 
  
def categorias(item):
  logger.info()
  itemlist = []
  
  data = httptools.downloadpage(item.url).data
  #logger.info("channels.cumlouder data="+data)
  patron  = '<a tag-url="[^"]+" class="[^"]+" href="([^"]+)" title="([^"]+)">[^<]+'
  patron += '<img class="thumb" src="([^"]+)" [^<]+<h2[^<]+<span[^<]+</span[^<]+<span[^<]+</span[^<]+'
  patron += '<span class="cantidad">([^"]+)</span>'
  
  matches = re.compile(patron, re.DOTALL).findall(data)
  for url,title,thumbnail, count in matches:
    itemlist.append(item.clone(title="%s (%s videos)" % (title, count), url=urlparse.urljoin(item.url,url), action ="videos", thumbnail = thumbnail))

  #Paginador
  matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
  if matches:
    itemlist.append(item.clone(title="Pagina Siguiente", url=urlparse.urljoin(item.url,matches[0])))

  return itemlist

def videos(item):
  logger.info()
  itemlist = []
  
  data = httptools.downloadpage(item.url).data
  
  patron = '<a class="muestra-escena" href="([^"]+)" title="([^"]+)"[^<]+<img class="thumb" src="([^"]+)".*?<span class="minutos"> <span class="ico-minutos sprite"></span> ([^<]+)</span>'
  
  matches = re.compile(patron, re.DOTALL).findall(data)
  for url, title, thumbnail, duration in matches:
    itemlist.append(item.clone(title="%s (%s)" % (title, duration), url=urlparse.urljoin(item.url,url), 
                                action ="play", thumbnail = thumbnail, contentThumbnail = thumbnail, 
                                contentType = "movie", contentTitle = title))
  
  #Paginador
  nextpage = scrapertools.find_single_match(data,'<ul class="paginador"(.*?)</ul>')
  matches = re.compile('<a href="([^"]+)" rel="nofollow">Next »</a>', re.DOTALL).findall(nextpage)
  if matches:
    itemlist.append(item.clone(title="Pagina Siguiente", url=urlparse.urljoin(item.url,matches[0])))
  else:
    matches = re.compile('<li[^<]+<a href="([^"]+)">Next »</a[^<]+</li>', re.DOTALL).findall(nextpage)
    if matches:
      itemlist.append(item.clone(title="Pagina Siguiente", url=urlparse.urljoin(item.url,matches[0])))
 
  return itemlist
    
def play(item):
  logger.info()
  itemlist = []
  
  data = httptools.downloadpage(item.url).data
  patron = '<source src="([^"]+)" type=\'video/([^\']+)\' label=\'[^\']+\' res=\'([^\']+)\' />'
  url,type,res = re.compile(patron, re.DOTALL).findall(data)[0]
  itemlist.append( Item(channel='cumlouder', action="play" , title='Video' +res, fulltitle=type.upper()+' '+res , url=url, server="directo", folder=False))
  
  return itemlist
