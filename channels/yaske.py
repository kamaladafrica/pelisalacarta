# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para yaske
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re, sys, urllib, urlparse

from core import config
from core import logger
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item

HOST = 'http://www.yaske.ro'

def mainlist(item):
    logger.info("pelisalacarta.yaske mainlist")
    itemlist = []
    
    itemlist.append( Item(channel=item.channel, title="Novedades"   , action="peliculas",             url=HOST))
    itemlist.append( Item(channel=item.channel, title="Por año"     , action="menu_buscar_contenido", url=HOST, extra="year"))
    itemlist.append( Item(channel=item.channel, title="Por género"  , action="menu_buscar_contenido", url=HOST, extra="gender"))
    itemlist.append( Item(channel=item.channel, title="Por calidad" , action="menu_buscar_contenido", url=HOST, extra="quality"))
    itemlist.append( Item(channel=item.channel, title="Por idioma"  , action="menu_buscar_contenido", url=HOST, extra="language"))
    itemlist.append( Item(channel=item.channel, title="Buscar"      , action="search") )

    return itemlist

def search(item,texto):
    logger.info("channels.pelisalacarta.yaske search")
    itemlist = []

    try:
        item.url = HOST+"/search/%s"
        item.url = item.url % texto
        item.extra = ""
        itemlist.extend(peliculas(item))
        itemlist = sorted(itemlist, key=lambda Item: Item.title) 

        return itemlist

    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []


def newest(categoria):
    logger.info("channels.yaske newest")
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = HOST+"/"
        elif categoria == 'infantiles':
            item.url = HOST+"/custom/?gender=animation"
        else:
            return []

        itemlist = peliculas(item)
        if itemlist[-1].title == ">> Página siguiente":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def peliculas(item):
    logger.info("channels.yaske peliculas")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    patron  = '<li class="item-movies.*?'
    patron += '<a class="image-block" href="([^"]+)" title="([^"]+)">'
    patron += '<img src="([^"]+).*?'
    patron += '<ul class="bottombox">.*?<li>(<img.*?)</li>.*?</ul>'
    patron += '<div class="quality">([^<]+)</div>'
 
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail, idiomas, calidad in matches:

        patronidiomas = "<img src='[^']+' title='([^']+)'"
        matchesidiomas = re.compile(patronidiomas,re.DOTALL).findall(idiomas)

        idiomas_disponibles = ""
        for idioma in matchesidiomas:
            idiomas_disponibles = idiomas_disponibles + idioma.strip() + "/"

        if len(idiomas_disponibles)>0:
            idiomas_disponibles = "["+idiomas_disponibles[:-1]+"]"
        
        title = scrapedtitle.strip()+" "+idiomas_disponibles+"["+calidad+"]"
        title = scrapertools.htmlclean(title)
        contentTitle = scrapertools.htmlclean(scrapedtitle.strip())
        url = scrapedurl
        thumbnail = scrapedthumbnail
        scrapedplot = ""

        itemlist.append( Item(channel=item.channel, action="findvideos", title=title , url=url , thumbnail=thumbnail , plot=scrapedplot , fulltitle=scrapertools.htmlclean(scrapedtitle.strip()), viewmode="movie", folder=True, hasContentDetails="true", contentTitle=contentTitle, contentThumbnail=thumbnail) )

    # Extrae el paginador
    patronvideos  = "<a href='([^']+)'>\&raquo\;</a>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=item.channel, action="peliculas", title=">> Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def menu_buscar_contenido(item):
    logger.info("channels.yaske menu_categorias")

    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<select name="'+item.extra+'"(.*?)</select>')
    # Extrae las entradas
    patron  = "<option value='([^']+)'>([^<]+)</option>"
    matches = re.compile(patron,re.DOTALL).findall(data)

    itemlist = []

    for scrapedurl,scrapedtitle in matches:
        scrapedthumbnail = ""
        scrapedplot = ""        
        
        if item.extra == 'gender':
            url = HOST+"/genero/"+scrapedurl
        else:
            url = HOST+"/custom/?"+item.extra+"="+scrapedurl

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=url , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return sorted(itemlist, key=lambda i:  i.title.lower())

def findvideos(item):
    logger.info("channels.yaske findvideos url="+item.url)

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    item.plot = scrapertools.find_single_match(data,'<meta name="sinopsis" content="([^"]+)"')
    item.plot = scrapertools.htmlclean(item.plot)
    item.contentPlot = item.plot

    patron  = '<tr bgcolor=(.*?)</tr>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    itemlist = []

    #n = 1
    for tr in matches:
        logger.info("tr="+tr)
        try:
            title = scrapertools.get_match(tr,'<b>([^<]+)</b>')
            server = scrapertools.get_match(tr,'"http\://www.google.com/s2/favicons\?domain\=([^"]+)"')

            # <td align="center"><img src="http://www.yaske.net/theme/01/data/images/flags/la_la.png" width="19">Lat.</td>
            idioma = scrapertools.get_match(tr,'<img src="http://www.yaske.[a-z]+/theme/01/data/images/flags/([a-z_]+).png"[^>]+>[^<]*<')
            subtitulos = scrapertools.get_match(tr,'<img src="http://www.yaske.[a-z]+/theme/01/data/images/flags/[^"]+"[^>]+>([^<]*)<')
            calidad = scrapertools.get_match(tr,'<td align="center" class="center"[^<]+<span title="[^"]*" style="text-transform.capitalize.">([^<]+)</span></td>')
            
            #<a [....] href="http://api.ysk.pe/noref/?u=< URL Vídeo >">
            url = scrapertools.get_match(tr,'<a.*?href="([^"]+)"')

            # Para extraer netutv se necesita en la actualidad pasar por varias páginas con lo que relentiza mucho la carga.
            # De momento mostrará "No hay nada que reproducir"
            '''
            if "/netu/tv/" in url:
                import base64
                ###################################################
                # Añadido 17-09-14
                ###################################################
                try: data = scrapertools.cache_page(url,headers=getSetCookie(url1))
                except: data = scrapertools.cache_page(url)
                ###################################################
                match_b64_1 = 'base64,([^"]+)"'
                b64_1 = scrapertools.get_match(data, match_b64_1)
                utf8_1 = base64.decodestring(b64_1)
                match_b64_inv = "='([^']+)';"
                b64_inv = scrapertools.get_match(utf8_1, match_b64_inv)
                b64_2 = b64_inv[::-1]
                utf8_2 = base64.decodestring(b64_2).replace("%","\\").decode('unicode-escape')
                id_video = scrapertools.get_match(utf8_2,'<input name="vid" id="text" value="([^"]+)">')
                url = "http://netu.tv/watch_video.php?v="+id_video
            '''

            title = title.replace("&nbsp;","")

            if "es_es" in idioma:
                scrapedtitle = title + " en "+server.strip()+" [ESP]["+calidad+"]"
            elif "la_la" in idioma:
                scrapedtitle = title + " en "+server.strip()+" [LAT]["+calidad+"]"
            elif "en_es" in idioma:
                scrapedtitle = title + " en "+server.strip()+" [SUB]["+calidad+"]"
            elif "en_en" in idioma:
                scrapedtitle = title + " en "+server.strip()+" [ENG]["+calidad+"]"
            else:
                scrapedtitle = title + " en "+server.strip()+" ["+idioma+" / "+subtitulos+"]["+calidad+"]"
            scrapedtitle = scrapertools.entityunescape(scrapedtitle)
            scrapedtitle = scrapedtitle.strip()

            scrapedurl = url

            scrapedthumbnail = servertools.guess_server_thumbnail(scrapedtitle)

            logger.info("server="+server+", scrapedurl="+scrapedurl)
            if scrapedurl.startswith("http") and not "olimpo.link" in scrapedurl:
                itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , folder=False, parentContent=item) )
        except:
            import traceback
            logger.info("Excepcion: "+traceback.format_exc())

    return itemlist

def play(item):
    logger.info("channels.yaske play item.url="+item.url)
    
    itemlist=[]

    # http%3A%2F%2Folo.gg%2Fs%2FcJinsNv1%3Fs%3Dhttp%253A%252F%252Fwww.nowvideo.to%252Fvideo%252F9c8bf2ed9d4fd
    data = urllib.unquote(item.url)

    logger.info("pelisalacarta.yaske play item.url="+data)

    # http://olo.gg/s/cJinsNv1?s=http%3A%2F%2Fwww.nowvideo.to%2Fvideo%2F9c8bf2ed9d4fd
    newdata = scrapertools.find_single_match(data,'olo.gg/s/[a-zA-Z0-9]+.s.(.*?)$')
    if newdata!="":
        data = newdata
    logger.info("pelisalacarta.yaske play item.url="+data)

    data = urllib.unquote(data)
    logger.info("pelisalacarta.yaske play item.url="+data)

    itemlist = servertools.find_video_items(item=item,data=data)
    for newitem in itemlist:
        newitem.fulltitle = item.fulltitle
    
    return itemlist
