# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para animeid
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
CHANNEL_HOST = "http://animeid.tv/"


def mainlist(item):
    logger.info("pelisalacarta.channels.animeid mainlist")
    
    itemlist = []
    itemlist.append( Item(channel=item.channel, action="novedades_series"    , title="Últimas series"     , url="http://www.animeid.tv/" ))
    itemlist.append( Item(channel=item.channel, action="novedades_episodios" , title="Últimos episodios"  , url="http://www.animeid.tv/" ))
    itemlist.append( Item(channel=item.channel, action="generos"             , title="Listado por genero" , url="http://www.animeid.tv/" ))
    itemlist.append( Item(channel=item.channel, action="letras"              , title="Listado alfabetico" , url="http://www.animeid.tv/" ))
    itemlist.append( Item(channel=item.channel, action="search"              , title="Buscar..." ))

    return itemlist

def newest(categoria):
    itemlist = []
    item = Item()
    try:
        if categoria == 'anime':
            item.url = "http://animeid.tv/"
            itemlist= novedades_episodios(item)
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist

def search(item,texto):
    logger.info("pelisalacarta.channels.animeid search")
    itemlist = []

    if item.url=="":
        item.url="http://www.animeid.tv/ajax/search?q="
    texto = texto.replace(" ","+")
    item.url = item.url+texto
    try:
        headers = []
        headers.append(["User-Agent","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0"])
        headers.append(["Referer","http://www.animeid.tv/"])
        headers.append(["X-Requested-With","XMLHttpRequest"])
        data = scrapertools.cache_page(item.url, headers=headers)
        data = data.replace("\\","")
        if DEBUG: logger.info("data="+data)
        
        patron = '{"id":"([^"]+)","text":"([^"]+)","date":"[^"]*","image":"([^"]+)","link":"([^"]+)"}'
        matches = re.compile(patron,re.DOTALL).findall(data)
        
        for id,scrapedtitle,scrapedthumbnail,scrapedurl in matches:
            title = scrapedtitle
            url = urlparse.urljoin(item.url,scrapedurl)
            thumbnail = scrapedthumbnail
            plot = ""
            if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")

            itemlist.append( Item(channel=item.channel, action="episodios" , title=title , url=url, thumbnail=thumbnail, plot=plot, show=title))

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def novedades_series(item):
    logger.info("pelisalacarta.channels.animeid novedades_series")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    data = scrapertools.get_match(data,'<section class="series">(.*?)</section>')
    patronvideos  = '<li><a href="([^"]+)"><span class="tipo\d+">([^<]+)</span><strong>([^<]+)</strong>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    itemlist = []
    
    for url,tipo,title in matches:
        scrapedtitle = title+" ("+tipo+")"
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=item.channel, action="episodios" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=title))

    return itemlist

def novedades_episodios(item):
    logger.info("pelisalacarta.channels.animeid novedades_episodios")

    # Descarga la pagina
    #<article> <a href="/ver/uchuu-kyoudai-35"> <header>Uchuu Kyoudai #35</header> <figure><img src="http://static.animeid.com/art/uchuu-kyoudai/normal/b4934a1d.jpg" class="cover" alt="Uchuu Kyoudai" width="250" height="140" /></figure><div class="mask"></div> <aside><span class="p"><strong>Reproducciones: </strong>306</span> <span class="f"><strong>Favoritos: </strong>0</span></aside> </a> <p>Una noche en el año 2006, cuando eran jovenes, los dos hermanos Mutta (el mayor) y Hibito (el menor) vieron un OVNI que hiba en dirección hacia la luna. Esa misma noche decidieron que ellos se convertirian en astronautas y irian al espacio exterior. En el año 2050, Hibito se ha convertido en astronauta y que ademas está incluido en una misión que irá a la luna. En cambio Mutta siguió una carrera mas tradicional, y terminó trabajando en una compañia de fabricación de automoviles. Sin embargo, Mutta termina arruinando su carrera por ciertos problemas que tiene con su jefe. Ahora bien, no sólo perdió su trabajo si no que fue incluido en la lista negra de la industria laboral. Pueda ser que esta sea su unica oportunidad que tenga Mutta de volver a perseguir su sueño de la infancia y convertirse en astronauta, al igual que su perqueño hermano Hibito.</p> </article>
    #<img pagespeed_high_res_src="
    data = scrapertools.cache_page(item.url)
    data = scrapertools.get_match(data,'<section class="lastcap">(.*?)</section>')

    patronvideos  = '<article> <a href="([^"]+)"> <header>([^<]+)</header> <figure><img[\sa-z_]+src="([^"]+)"[^<]+</figure><div[^<]+</div[^<]+<aside[^<]+<span class="p"[^<]+<strong[^<]+</strong[^<]+</span[^<]+<span[^<]+<strong[^<]+</strong[^<]+</span[^<]+</aside[^<]+</a[^<]+<p>(.*?)</p>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    itemlist = []
    
    for url,title,thumbnail,plot in matches:
        scrapedtitle = scrapertools.entityunescape(title)
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedthumbnail = thumbnail
        scrapedplot = plot
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        episodio = scrapertools.get_match(scrapedtitle,'\s+#(\d+)$')
        contentTitle = scrapedtitle.replace('#'+ episodio, '')

        itemlist.append( Item(channel=item.channel, action="findvideos" , title=scrapedtitle , url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot, viewmode="movie_with_plot",
                              hasContentDetails="true", contentSeason=1, contentTitle=contentTitle,
                              contentEpisodeNumber=int(episodio)))

    return itemlist

def generos(item):
    logger.info("pelisalacarta.channels.animeid generos")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    data = scrapertools.get_match(data,'<div class="generos">(.*?)</div>')
    patronvideos  = '<li> <a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    itemlist = []
    
    for url,title in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=item.channel, action="series" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=title))

    return itemlist

def letras(item):
    logger.info("pelisalacarta.channels.animeid letras")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    data = scrapertools.get_match(data,'<ul id="letras">(.*?)</ul>')
    patronvideos  = '<li> <a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    itemlist = []
    
    for url,title in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=item.channel, action="series" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=title))

    return itemlist

def series(item):
    logger.info("pelisalacarta.channels.animeid series")

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    '''
    <article class="item"> <a href="/aoi-sekai-no-chuushin-de"><header>Aoi Sekai no Chuushin de</header> <figure><img src="http://static.animeid.com/art/aoi-sekai-no-chuushin-de/cover/0077cb45.jpg" width="116" height="164" /></figure><div class="mask"></div></a> <p>El Reino de Segua ha ido perdiendo la guerra contra el Imperio de Ninterdo pero la situación ha cambiado con la aparición de un chico llamado Gear. Todos los personajes son parodias de protas de videojuegos de Nintendo y Sega respectivamente, como lo son Sonic the Hedgehog, Super Mario Bros., The Legend of Zelda, etc.</p> </article>
    '''
    patron  = '<article class="item"[^<]+'
    patron += '<a href="([^"]+)"[^<]+<header>([^<]+)</header[^<]+'
    patron += '<figure><img[\sa-z_]+src="([^"]+)"[^<]+</figure><div class="mask"></div></a> <p>(.*?)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    
    for url,title,thumbnail,plot in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedthumbnail = thumbnail
        scrapedplot = plot
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=item.channel, action="episodios" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=scrapedtitle, viewmode="movie_with_plot"))

    itemlist = sorted(itemlist, key=lambda item: item.title)

    try:
        page_url = scrapertools.get_match(data,'<li><a href="([^"]+)">&gt;</a></li>')
        itemlist.append( Item(channel=item.channel, action="series" , title=">> Página siguiente" , url=urlparse.urljoin(item.url,page_url), thumbnail="", plot=""))
    except:
        pass

    return itemlist

def episodios(item,final=True):
    logger.info("pelisalacarta.channels.animeid episodios")

    # Descarga la pagina
    body = scrapertools.cache_page(item.url)

    try:
        scrapedplot = scrapertools.get_match(body,'<meta name="description" content="([^"]+)"')
    except:
        pass

    try:
        scrapedthumbnail = scrapertools.get_match(body,'<link rel="image_src" href="([^"]+)"')
    except:
        pass

    data = scrapertools.get_match(body,'<ul id="listado">(.*?)</ul>')
    patron  = '<li><a href="([^"]+)">(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    
    for url,title in matches:
        scrapedtitle = scrapertools.htmlclean(title)

        try:
            episodio = scrapertools.get_match(scrapedtitle,"Capítulo\s+(\d+)")
            titulo_limpio = re.compile("Capítulo\s+(\d+)\s+",re.DOTALL).sub("",scrapedtitle)
            if len(episodio)==1:
                scrapedtitle = "1x0"+episodio+" - "+titulo_limpio
            else:
                scrapedtitle = "1x"+episodio+" - "+titulo_limpio
        except:
            pass

        scrapedurl = urlparse.urljoin(item.url,url)
        #scrapedthumbnail = ""
        #scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=item.channel, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=item.show, viewmode="movie_with_plot"))

    try:
        next_page = scrapertools.get_match(body,'<a href="([^"]+)">\&gt\;</a>')
        next_page = urlparse.urljoin(item.url,next_page)
        item2 = Item(channel=item.channel, action="episodios" , title=item.title , url=next_page, thumbnail=item.thumbnail, plot=item.plot, show=item.show, viewmode="movie_with_plot")
        itemlist.extend( episodios(item2,final=False) )
    except:
        import traceback
        logger.info(traceback.format_exc())

    if final and config.get_library_support():
        itemlist.append( Item(channel=item.channel, title="Añadir esta serie a la biblioteca de XBMC", url=item.url, action="add_serie_to_library", extra="episodios", show=item.show) )
        itemlist.append( Item(channel=item.channel, title="Descargar todos los episodios de la serie", url=item.url, action="download_all_episodes", extra="episodios", show=item.show) )

    return itemlist

def findvideos(item):
    logger.info("pelisalacarta.channels.animeid findvideos")

    data = scrapertools.cache_page(item.url)
    itemlist=[]
    
    url_anterior = scrapertools.find_single_match(data, '<li class="b"><a href="([^"]+)">« Capítulo anterior')
    url_siguiente = scrapertools.find_single_match(data, '<li class="b"><a href="([^"]+)">Siguiente capítulo »')
        
    if 'infoLabels' in item:
		del item.infoLabels
    
    data = scrapertools.find_single_match(data,'<ul id="partes">(.*?)</ul>')
    data = data.replace("\\/","/")
    data = data.replace("%3A",":")
    data = data.replace("%2F","/")
    logger.info("pelisalacarta.channels.animeid data="+data)

    #http%3A%2F%2Fwww.animeid.moe%2Fstream%2F41TLmCj7_3q4BQLnfsban7%2F1440956023.mp4
    #http://www.animeid.moe/stream/41TLmCj7_3q4BQLnfsban7/1440956023.mp4
    #http://www.animeid.tv/stream/oiW0uG7yqBrg5TVM5Cm34n/1385370686.mp4
    patron  = '(http://www.animeid.tv/stream/[^/]+/\d+.[a-z0-9]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    encontrados = set()
    for url in matches:
        if url not in encontrados:
            itemlist.append( Item(channel=item.channel, action="play" , title="[directo]" , server="directo", url=url, thumbnail="", plot="", show=item.show, folder=False))
            encontrados.add(url)

    from core import servertools
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        videoitem.channel=item.channel
        videoitem.action="play"
        videoitem.folder=False
        videoitem.title = "["+videoitem.server+"]"
        
    if url_anterior:
        title_anterior = url_anterior.replace("/ver/", '').replace('-', ' ').replace('.html', '')
        itemlist.append(Item(channel=item.channel, action="findvideos", title="Anterior: " + title_anterior,
                        url=CHANNEL_HOST + url_anterior, thumbnail=item.thumbnail, plot=item.plot, show=item.show,
                        fanart=item.thumbnail, folder=True))

    if url_siguiente:
        title_siguiente = url_siguiente.replace("/ver/", '').replace('-', ' ').replace('.html', '')
        itemlist.append(Item(channel=item.channel, action="findvideos", title="Siguiente: " + title_siguiente,
                        url=CHANNEL_HOST + url_siguiente, thumbnail=item.thumbnail, plot=item.plot, show=item.show,
                        fanart=item.thumbnail, folder=True))
    return itemlist

# Verificación automática de canales: Esta función debe devolver "True" si todo está ok en el canal.
def test():
    bien = True
    
    # mainlist
    mainlist_items = mainlist(Item())

    # Comprueba que todas las opciones tengan algo (excepto el buscador)
    for mainlist_item in mainlist_items:
        if mainlist_item.action!="search":
            exec "itemlist = "+mainlist_item.action+"(mainlist_item)"
            if len(itemlist)==0:
                return False

    # Da por bueno el canal si alguno de los vídeos de las series en "Destacados" devuelve mirrors
    episodios_items = novedades_episodios(mainlist_items[0])
    bien = False
    for episodio_item in episodios_items:
        mirrors = findvideos(episodio_item)
        if len(mirrors)>0:
            bien = True
            break
    
    return bien
