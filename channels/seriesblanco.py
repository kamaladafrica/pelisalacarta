# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools


__channel__ = "seriesblanco"

__category__ = "F"

__type__ = "generic"

__title__ = "Series Blanco"

__language__ = "ES"


host = "http://seriesblanco.com/"

idiomas = {'es':'Español','la':'Latino','vos':'VOS','vo':'VO', 'japovose':'VOSE'}


DEBUG = config.get_setting("debug")
def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.seriesblanco mainlist")

    itemlist = []
    itemlist.append( Item( channel=__channel__, title="Series", action="series", url=urlparse.urljoin(host,"lista_series/") ) )
    itemlist.append( Item( channel=__channel__, title="Buscar...", action="search", url=host) )

    return itemlist

def search(item,texto):
    logger.info("[pelisalacarta.seriesblanco search texto="+texto)

    itemlist = []

    item.url = urlparse.urljoin(host,"/search.php?q1=%s" % (texto))
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s","",data)
    data = re.sub(r"<!--.*?-->","",data)
    data = unicode( data, "iso-8859-1" , errors="replace" ).encode("utf-8")

    #<div style='float:left;width: 620px;'><div style='float:left;width: 33%;text-align:center;'><a href='/serie/20/against-the-wall.html' '><img class='ict' src='http://4.bp.blogspot.com/-LBERI18Cq-g/UTendDO7iNI/AAAAAAAAPrk/QGqjmfdDreQ/s320/Against_the_Wall_Seriesdanko.jpg' alt='Capitulos de: Against The Wall' height='184' width='120'></a><br><div style='text-align:center;line-height:20px;height:20px;'><a href='/serie/20/against-the-wall.html' style='font-size: 11px;'> Against The Wall</a></div><br><br>

    patron = "<div style='text-align:center;line-height:20px;height:20px;'><a href='([^']+)' style='font-size: 11px;'>([^<]+)</a>"

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append( Item(channel=__channel__, title =scrapedtitle , url=urlparse.urljoin(host,scrapedurl), action="episodios", show=scrapedtitle) )

    try:
        return itemlist
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def series(item):
    logger.info("pelisalacarta.seriesblanco series")

    itemlist = []

    # Descarga la página
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s","",data)
    data = re.sub(r"<!--.*?-->","",data)
    data = unicode( data, "iso-8859-1" , errors="replace" ).encode("utf-8")

    patron = "<li><a href='([^']+)' title='([^']+)'>[^<]+</a></li>"

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append( Item(channel=__channel__, title =scrapedtitle , url=urlparse.urljoin(host,scrapedurl), action="episodios", show=scrapedtitle) )

    return itemlist

def episodios(item):
    logger.info("pelisalacarta.seriesblanco episodios")

    itemlist = []

    # Descarga la página
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s","",data)
    data = re.sub(r"<!--.*?-->","",data)
    data = unicode( data, "iso-8859-1" , errors="replace" ).encode("utf-8")

    data = re.sub(r"a></td><td> <img src=/banderas/","a><idioma/",data)
    data = re.sub(r"<img src=/banderas/","|",data)
    data = re.sub(r"\.png border='\d+' height='\d+' width='\d+'[^>]+><","/idioma><",data)
    data = re.sub(r"\.png border='\d+' height='\d+' width='\d+'[^>]+>","",data)

    #<a href='/serie/534/temporada-1/capitulo-00/the-big-bang-theory.html'>1x00 - Capitulo 00 </a></td><td> <img src=/banderas/vo.png border='0' height='15' width='25' /> <img src=/banderas/vos.png border='0' height='15' width='25' /></td></tr>

    patron = "<a href='([^']+)'>([^<]+)</a><idioma/([^/]+)/idioma>"

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedidioma in matches:
        idioma = ""
        for i in scrapedidioma.split("|"):
            idioma+= " [" + idiomas[i] + "]"
        title = item.title + " - " + scrapedtitle + idioma
        itemlist.append( Item(channel=__channel__, title =title , url=urlparse.urljoin(host,scrapedurl), action="findvideos", show=item.show) )

    if len(itemlist) == 0 and "<title>404 Not Found</title>" in data:
        itemlist.append( Item(channel=__channel__, title ="la url '"++"' parece no estar disponible en la web. Iténtalo más tarde." , url=item.url, action="series") )

    ## Opción "Añadir esta serie a la biblioteca de XBMC"
    if config.get_library_support() and len(itemlist)>0:
        itemlist.append( Item(channel=__channel__, title="Añadir esta serie a la biblioteca de XBMC", url=item.url, action="add_serie_to_library", extra="episodios", show=item.show) )

    return itemlist

def findvideos(item):
    logger.info("pelisalacarta.seriesblanco findvideos")

    itemlist = []

    # Descarga la página
    data = scrapertools.cache_page(item.url)

    # Hacer la petición ajax con los enlaces
    params = scrapertools.get_match(data, 'data : "(action=load[^\"]+)"')
    data = scrapertools.cachePagePost(host + 'ajax.php', params)

    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s","",data)
    data = re.sub(r"<!--.*?-->","",data)
    data = unicode( data, "iso-8859-1" , errors="replace" ).encode("utf-8")

    data = re.sub(r"<center>|</center>|</a>", "", data)
    data = re.sub(r'<div class="grid_content([^>]+)><span></span>',r'<div class="grid_content\1><span>SD</span>', data)

    '''
    <td><div class="grid_content*ATTR*><span>(*FECHA*)</span></div></td>
    <td>
    <div class="grid_content2*ATTR*><span><img src="*PATH*/(*IDIOMA*)\.*ATTR*></span></td>
    <td><div class="grid_content*ATTR*><span><a href="(*ENLACE*)"*ATTR*><img src='/servidores/(*SERVIDOR*).*ATTR*></span></div></td>"
    <td>
    <div class="grid_content*ATTR*><span>(*UPLOADER*)</span></td>
    <td>
    <div class="grid_content*ATTR*><span>(*SUB|CALIDAD*)</span></td>
    '''

    online = scrapertools.get_match(data, '<table class="as_gridder_table">(.+?)</table>')
    download = scrapertools.get_match(data, '<div class="grid_heading"><h2>Descarga</h2></div>(.*)')

    online = re.sub(
        r"<td><div class=\"grid_content[^>]+><span>([^>]+)</span></div></td>" + \
         "<td>" + \
         "<div class=\"grid_content2[^>]+><span><img src=\".+?banderas/([^\.]+)\.[^>]+></span></td>" + \
         "<td><div class=\"grid_content[^>]+><span><a href=\"([^\"]+)\"[^>]+><img src='/servidores/([^\.]+)\.[^>]+></span></div></td>" + \
         "<td>" + \
         "<div class=\"grid_content[^>]+><span>([^>]+)</span></td>" + \
         "<td>" + \
         "<div class=\"grid_content[^>]+><span>([^>]+)</span></td>",
        r"<patron>\3;\2;\1;\4;\5;\6;Ver</patron>",
        online
    )

    download = re.sub(
        r"<td><div class=\"grid_content[^>]+><span>([^>]+)</span></div></td>" + \
         "<td>" + \
         "<div class=\"grid_content2[^>]+><span><img src=\".+?banderas/([^\.]+)\.[^>]+></span></td>" + \
         "<td><div class=\"grid_content[^>]+><span><a href=\"([^\"]+)\"[^>]+><img src='/servidores/([^\.]+)\.[^>]+></span></div></td>" + \
         "<td>" + \
         "<div class=\"grid_content[^>]+><span>([^>]+)</span></td>" + \
         "<td>" + \
         "<div class=\"grid_content[^>]+><span>([^>]+)</span></td>",
        r"<patron>\3;\2;\1;\4;\5;\6;Descargar</patron>",
        download
    )

    data = online+download

    '''
    <patron>*URL*;*IDIOMA*;*FECHA*;*SERVIDOR*;*UPLOADER*;*SUB|CALIDAD*;*TIPO*</patron>
    '''

    patron = '<patron>([^;]+);([^;]+);([^;]+);([^;]+);([^;]+);([^;]+);([^<]+)</patron>'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedidioma, scrapedfecha, scrapedservidor, scrapeduploader, scrapedsubcalidad, scrapedtipo in matches:
        title = scrapedtipo + " en " + scrapedservidor + " [" + idiomas[scrapedidioma] + "] [" + scrapedsubcalidad + "] (" + scrapeduploader + ": "+ scrapedfecha + ")"
        itemlist.append( Item(channel=__channel__, title =title , url=urlparse.urljoin(host,scrapedurl), action="play", show=item.show) )

    return itemlist

def play(item):
    logger.info("pelisalacarta.channels.seriesblanco play url="+item.url)

    data = scrapertools.cache_page(item.url)

    patron = "<input type='button' value='Ver o Descargar' onclick='window.open\(\"([^\"]+)\"\);'/>"
    url = scrapertools.find_single_match(data,patron)

    itemlist = servertools.find_video_items(data=url)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.channel = __channel__

    return itemlist    
