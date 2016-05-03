# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documaniatv.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os,sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools
from core import jsontools

__channel__ = "documaniatv"
__category__ = "D"
__type__ = "generic"
__title__ = "DocumaniaTV"
__language__ = "ES"

DEBUG = config.get_setting("debug")

def isGeneric():
    return True

def mainlist(item):
    logger.info("[documaniatv.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=__channel__, action="novedades"  , title="Novedades"      , url="http://www.documaniatv.com"))
    itemlist.append( Item(channel=__channel__, action="categorias" , title="Por categorías" , url="http://www.documaniatv.com"))
    itemlist.append( Item(channel=__channel__, action="novedades"  , title="Top"      , url="http://www.documaniatv.com/topvideos.html"))
    itemlist.append( Item(channel=__channel__, action="canales" , title="Por canales" , url="http://www.documaniatv.com"))
    itemlist.append( Item(channel=__channel__, action="viendo" , title="Viendo ahora" , url="http://www.documaniatv.com"))
    itemlist.append( Item(channel=__channel__, action="search"     , title="Buscar"))
    return itemlist

def novedades(item):
    logger.info("[documaniatv.py] novedades")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    logger.info(data)
    matches = re.compile('<li[^<]+<div class="pm-li-video">(.*?)</li>',re.DOTALL).findall(data)
    
    for match in matches:
        logger.info(str(match))
        try:

            #logger.info(match)
            scrapedtitle = scrapertools.get_match(match,'title="(.*?)"')
            #logger.info("scrapedtitle")
            #logger.info(scrapedtitle)
            scrapedurl = scrapertools.get_match(match,'<a href="(.*?)"')
            #logger.info(scrapedurl)
            scrapedthumbnail = scrapertools.get_match(match,'<img src="(.*?)"')
            #logger.info(scrapedthumbnail)
            scrapedplot = scrapertools.find_single_match(match,'<p class="pm-video-attr-desc">(.*?)</p>')
            #scrapedplot = scrapertools.htmlclean(scrapedplot)
            scrapedplot = scrapertools.entityunescape(scrapedplot)
            #logger.info(scrapedplot)
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

            itemlist.append( Item(channel=__channel__, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , fanart=scrapedthumbnail, folder=False) )

        except:
            logger.info("documaniatv.novedades Error al añadir entrada "+match)
            pass


    # Busca enlaces de paginas siguientes...
    try:
        next_page_url = scrapertools.get_match(data,'<li class="active"[^<]+<a[^<]+</a[^<]+</li[^<]+<li[^<]+<a href="([^"]+)">')
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=__channel__, action="novedades", title=">> Pagina siguiente" , url=next_page_url , thumbnail="" , plot="" , folder=True) )
    except:
        logger.info("documaniatv.novedades Siguiente pagina no encontrada")
    
    return itemlist

def categorias(item):
    logger.info("[documaniatv.py] categorias")
    itemlist = []
    
    data = scrapertools.cache_page(item.url)
    data = data.replace("\n","")

    # Saca el bloque con las categorias
    data = scrapertools.get_match(data,"Categorias<b(.*?)</ul></li>")

    #
    patron = '<li[^<]+<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        #itemlist.append( Item(channel=__channel__ , action="novedades" , title=match[1],url="http://www.documaniatv.com"+match[0]))
        itemlist.append( Item(channel=__channel__ , action="novedades" , title=match[1],url=match[0]))
        
    return itemlist


def tags(item):
    logger.info("[documaniatv.py] categorias")
    itemlist = []

    # Saca el bloque con las categorias
    data = scrapertools.cache_page(item.url)
    data = scrapertools.get_match(data,'<h4>Palabras Clave</h4>(.*?)</div>')

    #
    patron = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        itemlist.append( Item(channel=__channel__ , action="novedades" , title=match[1],url="http://www.documaniatv.com"+match[0]))
    
    return itemlist

def canales(item):
    logger.info("[documaniatv.py] canales")
    itemlist = []

    # Saca el bloque con las categorias
    data = scrapertools.cache_page(item.url)
    #logger.info(data)
    data = scrapertools.get_match(data,"""Canales(.*?)</ul></li>""")
    #logger.error(data)

    #
    patron = '<li[^<]+<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        #itemlist.append( Item(channel=__channel__ , action="novedades" , title=match[1],url="http://www.documaniatv.com"+match[0]))
        itemlist.append( Item(channel=__channel__ , action="novedades" , title=match[1],url=match[0]))
    
    return itemlist


def viendo(item):
    logger.info("[documaniatv.py] viendo")
    itemlist = []

    # Saca el bloque con las categorias
    data = scrapertools.cache_page(item.url)
    logger.info(data)
    data = scrapertools.get_match(data,"""<ul class="pm-ul-wn-videos clearfix" id="pm-ul-wn-videos">(.*?)</ul>""")
    

    #
    patron = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    imgs= '<img src="([^"]+)"[^>]+>'
    matc = re.compile(imgs,re.DOTALL).findall(data)
    
    for match,m in zip(matches,matc):
        logger.error(str(match))
        itemlist.append( Item(channel=__channel__ , action="play" , title=match[1],url=match[0],thumbnail=m))
    
    return itemlist

def search(item,texto):
    #http://www.documaniatv.com/search.php?keywords=luna&btn=Buscar
    logger.info("[documaniatv.py] search")
    data = scrapertools.cache_page("http://www.documaniatv.com")
    cx = scrapertools.find_single_match(data, "var cx='([^']+)'")
    item.url="https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&cx=%s&q=%s&start=0"
    texto = texto.replace(" ","+")
    item.url = item.url % (cx, texto)
    try:
        return busqueda(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def busqueda(item):
    logger.info("[documaniatv.py] busqueda")
    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = jsontools.load_json(data)
    if int(data['cursor']['resultCount'].replace(".","")) == 0:
        itemlist.append( Item(channel=__channel__, action="", title="No hay resultados" , url="" , folder=False) )
        return itemlist
    for results in data['results']:
        try:
            scrapedurl = results['richSnippet']['metatags']['ogUrl']
            scrapedtitle = results['richSnippet']['metatags']['ogTitle']
            scrapedthumbnail = results['richSnippet']['metatags']['ogImage']
            scrapedplot = results['richSnippet']['videoobject']['description']
            if "/tags/" in scrapedurl:
                action = "novedades"
            else:
                action = "play"
        except:
            scrapedurl = results['unescapedUrl']
            scrapedtitle = results['titleNoFormatting']
            scrapedthumbnail = ""
            scrapedplot = ""
            action = "novedades"
        itemlist.append( Item(channel=__channel__, action=action, title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , fanart=scrapedthumbnail, folder=True) )
    if int(data['cursor']['resultCount'].replace(".","")) > 10:
        page = int(scrapertools.find_single_match(item.url, 'start=(\d+)')) + 10
        if page <= 90:
            scrapedurl = re.sub(r'start=(\d+)','start='+str(page), item.url)
            itemlist.append( Item(channel=__channel__, action="busqueda", title=">> Siguiente página" , url=scrapedurl , folder=True) )
    return itemlist

def play(item):
    logger.info("documaniatv.play")
    itemlist = []

    data = scrapertools.cachePage(item.url)
    var_url, ajax = scrapertools.find_single_match(data, 'preroll_timeleft.*?url:([^+]+)\+"([^"]+)"')
    url_base = scrapertools.find_single_match(data, 'var.*?' + var_url + '="([^"]+)"')
    patron = 'preroll_timeleft.*?data:\{"([^"]+)":"([^"]+)","' \
             '([^"]+)":"([^"]+)","([^"]+)":"([^"]+)","([^"]+)"' \
             ':"([^"]+)","([^"]+)":"([^"]+)"\}'
    match = scrapertools.find_single_match(data, patron)
    params = "{0}={1}&{2}={3}&{4}={5}&{6}={7}&{8}={9}".format(match[0],match[1],match[2],
                                                              match[3],match[4],match[5],
                                                              match[6],match[7],match[8],
                                                              match[9])
    url = url_base + ajax + "?" + params
    data1 = scrapertools.cachePage(url)

    patron= '<iframe src="(.*?)"'
    match = re.compile(patron,re.DOTALL).findall(data1)
    logger.info(match[0])

    # Busca los enlaces a los videos
    video_itemlist = servertools.find_video_items(data=match[0])
    for video_item in video_itemlist:
        itemlist.append( Item(channel=__channel__ , action="play" , server=video_item.server, title=item.title+video_item.title,url=video_item.url, thumbnail=video_item.thumbnail, plot=video_item.plot, folder=False))

    return itemlist

# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    items = novedades(mainlist_items[0])
    bien = False
    for singleitem in items:
        mirrors = servertools.find_video_items( item=singleitem )
        if len(mirrors)>0:
            bien = True
            break

    return bien
