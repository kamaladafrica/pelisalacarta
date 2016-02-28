# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para Descargasmix
# Por SeiTaN, robalo y Cmos
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "descargasmix"
__category__ = "A"
__type__ = "generic"
__title__ = "Descargasmix"
__language__ = "ES"

DEBUG = config.get_setting("debug")

DEFAULT_HEADERS = ["User-Agent","Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12"]

def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.channels.descargasmix mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="Películas"      , action="lista", thumbnail= "http://i.imgur.com/tBTqIlV.jpg?1", fanart="http://i.imgur.com/c3HS8kj.png"))
    itemlist.append( Item(channel=__channel__, title="Series"         , action="entradas", url="http://descargasmix.net/series/", thumbnail= "http://i.imgur.com/tBTqIlV.jpg?1", fanart="http://i.imgur.com/9loVksV.png"))
    itemlist.append( Item(channel=__channel__, title="Documentales"   , action="entradas", url="http://descargasmix.net/documentales/", thumbnail= "http://i.imgur.com/tBTqIlV.jpg?1", fanart="http://i.imgur.com/Q7fsFI6.png"))
    itemlist.append( Item(channel=__channel__, title="Anime"          , action="entradas", url="http://descargasmix.net/anime/", thumbnail= "http://i.imgur.com/tBTqIlV.jpg?1", fanart="http://i.imgur.com/whhzo8f.png"))
    itemlist.append( Item(channel=__channel__, title="Deportes"       , action="entradas", url="http://descargasmix.net/deportes/", thumbnail= "http://i.imgur.com/tBTqIlV.jpg?1", fanart="http://i.imgur.com/ggFFR8o.png"))
    itemlist.append( Item(channel=__channel__, title="Buscar..."      , action="search"  , url="http://descargasmix.net/?s=", thumbnail= "http://i.imgur.com/tBTqIlV.jpg?1", extra= "Buscar"))
    return itemlist

def search(item,texto):
    logger.info("pelisalacarta.channels.descargasmix search")
    try:
        item.url= item.url + texto
        itemlist = busqueda(item)
        return itemlist
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []
def busqueda(item):
    logger.info("pelisalacarta.channels.descargasmix busqueda")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    bloque = scrapertools.find_single_match(data, '<div id="content" role="main">(.*?)<div id="sidebar" role="complementary">')
    patron = '<a class="clip-link".*?href="([^"]+)".*?<img alt="([^"]+)" src="([^"]+)"'
    patron += '.*?<p class="stats">(.*?)</p>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail,scrapedcat in matches:
        scrapedthumbnail = "http:"+scrapedthumbnail.replace("-129x180","")
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        if ("Películas" in scrapedcat) | ("Documentales" in scrapedcat):
            titulo = scrapedtitle.split("[")[0]
            itemlist.append( Item(channel=__channel__, action='findvideos', title= scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, fulltitle=titulo, context = "0", folder=True) )
        else:
            itemlist.append( Item(channel=__channel__, action='temporadas', title= scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, fulltitle=scrapedtitle, context = "2", folder=True) )

    patron = '<a class="nextpostslink".*?href="([^"]+)"'
    matches = scrapertools.find_single_match(data, patron)
    if len(matches) > 0:
        npage = scrapertools.find_single_match(matches,"page/(.*?)/")
        if DEBUG: logger.info("url=["+matches+"]")
        itemlist.append( Item(channel=__channel__, action='busqueda', title= "Página "+npage , url=matches ,folder=True) )

    return itemlist
	
def lista(item):
    logger.info("pelisalacarta.channels.descargasmix lista")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="Novedades"      , action="entradas"    , url="http://descargasmix.net/peliculas", thumbnail= item.thumbnail, fanart=item.fanart))
    itemlist.append( Item(channel=__channel__, title="Estrenos"       , action="entradas"    , url="http://descargasmix.net/peliculas/estrenos", thumbnail= item.thumbnail, fanart=item.fanart))
    itemlist.append( Item(channel=__channel__, title="Dvdrip"         , action="entradas"    , url="http://descargasmix.net/peliculas/dvdrip", thumbnail= item.thumbnail, fanart=item.fanart))
    itemlist.append( Item(channel=__channel__, title="HD (720p/1080p)", action="entradas"    , url="http://descargasmix.net/peliculas/hd", thumbnail= item.thumbnail, fanart=item.fanart))
    itemlist.append( Item(channel=__channel__, title="HDRIP"          , action="entradas"    , url="http://descargasmix.net/peliculas/hdrip", thumbnail= item.thumbnail, fanart=item.fanart))
    itemlist.append( Item(channel=__channel__, title="Latino"         , action="entradas"    , url="http://descargasmix.net/peliculas/latino-peliculas", thumbnail= item.thumbnail, fanart=item.fanart))
    itemlist.append( Item(channel=__channel__, title="VOSE"           , action="entradas"    , url="http://descargasmix.net/peliculas/subtituladas", thumbnail= item.thumbnail, fanart=item.fanart))
    itemlist.append( Item(channel=__channel__, title="3D"             , action="entradas"    , url="http://descargasmix.net/peliculas/3d", thumbnail= item.thumbnail, fanart=item.fanart))
    return itemlist

def entradas(item):
    logger.info("pelisalacarta.channels.descargasmix entradas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    bloque = scrapertools.find_single_match(data, '<div id="content" role="main">(.*?)<div id="sidebar" role="complementary">')
    contenido = ["series","deportes","anime"]
    c_match = [True for match in contenido if match in item.url]
    #Patron dependiendo del contenido
    if True in c_match:
        patron = '<a class="clip-link".*?href="([^"]+)".*?<img alt="([^"]+)" src="([^"]+)"'
        patron += '.*?<span class="overlay(|[^"]+)">'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedurl, scrapedtitle, scrapedthumbnail,scrapedinfo in matches:
            if scrapedinfo != "": scrapedinfo = " [[COLOR red]"+scrapedinfo.replace(" ","").replace("-", " ").capitalize()+"[/COLOR]]"
            titulo = scrapedtitle+scrapedinfo	
            titulo = scrapertools.decodeHtmlentities(titulo)
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
            scrapedthumbnail = "http:"+scrapedthumbnail.replace("-129x180","")
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append( Item(channel=__channel__, action='temporadas', title= titulo , url=scrapedurl , thumbnail=scrapedthumbnail, fanart=item.fanart, fulltitle=scrapedtitle, context = "2", folder=True) )
    else:
        patron = '<a class="clip-link".*?href="([^"]+)".*?<img alt="([^"]+)" src="([^"]+)"'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
            titulo = scrapertools.decodeHtmlentities(scrapedtitle)
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.split("[")[0])
            scrapedthumbnail = "http:"+scrapedthumbnail.replace("-129x180","")
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append( Item(channel=__channel__, action='findvideos', title= titulo , url=scrapedurl , thumbnail=scrapedthumbnail, fanart=item.fanart, fulltitle=scrapedtitle, context = "0", folder=True) )
    #Paginación
    patron = '<a class="nextpostslink".*?href="([^"]+)"'
    matches = scrapertools.find_single_match(data, patron)
    if len(matches) > 0:
        npage = scrapertools.find_single_match(matches,"page/(.*?)/")
        if DEBUG: logger.info("url=["+matches+"]")
        itemlist.append( Item(channel=__channel__, action='entradas', title= "Página "+npage , url=matches , fanart=item.fanart, folder=True) )

    return itemlist

def temporadas(item):
    logger.info("pelisalacarta.channels.descargasmix temporadas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    sinopsis = scrapertools.find_single_match(data, '<strong>SINOPSIS</strong>:(.*?)</p>')
    fanart = item.fanart
    try:
        sinopsis, fanart = info(item.fulltitle, "tv", sinopsis)
    except:
        pass
    patron = '<div class="season".*?>(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle in matches:
        itemlist.append( Item(channel=__channel__, action="episodios", title=scrapedtitle , fulltitle = item.fulltitle, url=item.url , thumbnail=item.thumbnail , fanart=fanart, plot=str(sinopsis), context = "2", folder=True) )
    return itemlist

def episodios(item):
    logger.info("pelisalacarta.channels.descargasmix episodios")
    itemlist = []
    fanart = item.fanart
    thumbnail = item.thumbnail
    try:
        from core.tmdb import Tmdb
        otmdb= Tmdb(texto_buscado=item.fulltitle, tipo="tv")
    except:
        pass
    data = scrapertools.cachePage(item.url)
    patron = item.title+'(.*?)</li>'
    bloque = scrapertools.find_single_match(data, patron)
    patron = '<h3 style="text-transform: uppercase;font-size: 18px;">(.*?)</h3>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedtitle in matches:
        try:
            if "Descargar" in scrapedtitle:
                titulo = "[COLOR sandybrown][B]"+scrapedtitle+"[/B][/COLOR]"
                item.plot, fanart, thumbnail = infoepi(otmdb, scrapedtitle.rsplit(' ', 1)[1])
            else:
                titulo = "[COLOR green][B]"+scrapedtitle+"[/B][/COLOR]"
                item.plot, fanart, thumbnail = infoepi(otmdb, scrapedtitle.rsplit(' ', 1)[1])
        except:
            pass
        try:
            fulltitle = item.fulltitle+match.split(item.fulltitle)[1]
            itemlist.append( Item(channel=__channel__, action="epienlaces", title=titulo, fulltitle = fulltitle, url=item.url , thumbnail=thumbnail , fanart=fanart, plot=str(item.plot), context = "2", extra=scrapedtitle, folder=True ))
        except:
            itemlist.append( Item(channel=__channel__, action="epienlaces", title=titulo, fulltitle = item.fulltitle, url=item.url , thumbnail=thumbnail , fanart=fanart, plot=str(item.plot), context = "2", extra=scrapedtitle, folder=True ))
    return itemlist

def epienlaces(item):
    logger.info("pelisalacarta.channels.descargasmix epienlaces")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = data.replace("\n","").replace("\t", "")

    #Bloque de enlaces si viene de enlaces de descarga u online
    delimitador = item.extra.replace("(","\(").replace(")","\)")
    if delimitador.startswith("Ver"):
        patron = delimitador+'</h3>(<div class="episode-server">.*?)(?:</li>|<div class="episode-title">)'
    else:
        patron = delimitador+'</h3><div class="episode-title">(.*?)(?:<h3 style="text-transform: uppercase;font-size: 18px;">|</li>)'
    bloque = scrapertools.find_single_match(data, patron)

    patron = '<div class="episode-server">.*?href="([^"]+)"'
    patron += '.*?data-server="([^"]+)"'
    patron += '.*?<div style="float:left;width:140px;">(.*?)</div>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedserver, scrapedcalidad in matches:
        if scrapedserver == "ul": scrapedserver = "uploadedto"
        titulo = scrapedserver.capitalize()+" ["+scrapedcalidad+"]"
        #Enlaces descarga
        if delimitador.startswith("Descargar"):
            if scrapedserver == "magnet":
                titulo = titulo.replace("Magnet", "[COLOR green][Enlace en Torrent][/COLOR]")
                itemlist.append( Item(channel=__channel__, action="play", title=titulo, server="torrent", url=scrapedurl , fulltitle = item.fulltitle, thumbnail=item.thumbnail , fanart=item.fanart, plot=item.plot, folder=False) )
            else:
                mostrar_server= True
                if config.get_setting("hidepremium")=="true":
                    mostrar_server= servertools.is_server_enabled (scrapedserver)
                if mostrar_server:
                    try:
                        servers_module = __import__("servers."+scrapedserver)
                        itemlist.append( Item(channel=__channel__, action="play_episodios", title=titulo , fulltitle = item.fulltitle, url=scrapedurl ,  thumbnail=item.thumbnail , fanart=item.fanart, plot=item.plot, extra=item.url, folder=True) )
                    except:
                        pass
            itemlist.sort(key=lambda item: item.title, reverse=True)
        #Enlaces online
        else:
            enlaces = servertools.findvideos(data=scrapedurl)
            if len(enlaces)> 0:
                titulo = "Enlace encontrado en [COLOR sandybrown]"+enlaces[0][0]+"[/COLOR] ["+scrapedcalidad+"]"
                itemlist.append( Item(channel=__channel__, action="play", server=enlaces[0][2], title=titulo , url=enlaces[0][1] , fulltitle = item.fulltitle, thumbnail=item.thumbnail , fanart=item.fanart, plot=item.plot, folder=False) )

    return itemlist

def play_episodios(item):
    logger.info("pelisalacarta.channels.descargasmix play_episodios")
    itemlist = []
    #IF en caso de redireccion
    if "http://descargasmix" in item.url:
        DEFAULT_HEADERS.append( ["Referer",item.extra] )
        data = scrapertools.cachePage(item.url,headers=DEFAULT_HEADERS)
        item.url = scrapertools.find_single_match(data,'src="([^"]+)"')
    enlaces = servertools.findvideos(data=item.url)
    if len(enlaces)> 0:
        titulo = "Enlace encontrado en "+enlaces[0][0]
        itemlist.append( Item(channel=__channel__, action="play", server=enlaces[0][2], title=titulo , url=enlaces[0][1] , fulltitle = item.fulltitle, thumbnail=item.thumbnail , fanart=item.fanart, plot=item.plot, folder=False) )
    return itemlist

def findvideos(item):
    logger.info("pelisalacarta.channels.descargasmix findvideos")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    sinopsis = scrapertools.find_single_match(data, '<strong>SINOPSIS</strong>:(.*?)</p>')
    fanart = item.fanart
    try:
        sinopsis, fanart = info(item.fulltitle, "movie", sinopsis)
    except:
        pass
    #Patron torrent
    patron = 'class="separate3 magnet".*?href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl in matches:
        itemlist.append( Item(channel=__channel__, action="play", server="torrent", title="[COLOR green][Enlace en Torrent][/COLOR]" , fulltitle = item.fulltitle, url=scrapedurl , thumbnail=item.thumbnail , fanart=fanart, plot=str(sinopsis) , context = "0", folder=False) )
    
    #Patron online
    data_online = scrapertools.find_single_match(data, 'Enlaces para ver online(.*?)<div class="section-box related-posts">')
    if len(data_online)> 0:
        patron = 'dm\(c.a\(\'([^\']+)\''
        matches = scrapertools.find_multiple_matches(data_online, patron)
        for code in matches:
            enlace = dm(code)
            enlaces = servertools.findvideos(data=enlace)
            titulo = "Enlace encontrado en [COLOR sandybrown]"+enlaces[0][0]+"[/COLOR]"
            if len(enlaces)> 0:
                itemlist.append( Item(channel=__channel__, action="play", server=enlaces[0][2], title=titulo, url=enlaces[0][1] , fulltitle = item.fulltitle, thumbnail=item.thumbnail , fanart=fanart, plot=str(sinopsis) , context = "0", folder=False) )

    #Patron descarga
    data_descarga = scrapertools.find_single_match(data, 'Enlaces de descarga(.*?)<script>')
    patron = '<div class="fondoenlaces".*?id=".*?_([^"]+)".*?textContent=nice=dm\(c.a\(\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data_descarga, patron)
    for scrapedserver, scrapedurl in matches:
        if (scrapedserver == "ul") | (scrapedserver == "uploaded"): scrapedserver = "uploadedto"
        titulo = scrapedserver.capitalize()
        if titulo == "Magnet":continue
        mostrar_server= True
        if config.get_setting("hidepremium")=="true":
            mostrar_server= servertools.is_server_enabled (scrapedserver)
        if mostrar_server:
            try:
                servers_module = __import__("servers."+scrapedserver)
                #Saca numero de enlaces
                patron = "(dm\(c.a\('"+scrapedurl.replace("+","\+")+"'.*?)</div>"
                data_enlaces = scrapertools.find_single_match(data_descarga, patron)
                patron = 'dm\(c.a\(\'([^\']+)\''
                matches_enlaces = scrapertools.find_multiple_matches(data_enlaces,patron)
                numero = str(len(matches_enlaces))
                itemlist.append( Item(channel=__channel__, action="enlaces", title=titulo+" - Nº enlaces:"+numero , url=item.url , fulltitle = item.fulltitle, thumbnail=item.thumbnail , fanart=fanart, plot=str(sinopsis) , extra=scrapedurl, context = "0", folder=True) )
            except:
                pass
    return itemlist
	
def enlaces(item):
    logger.info("pelisalacarta.channels.descargasmix enlaces")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    #Bloque de enlaces
    patron = "(dm\(c.a\('"+item.extra.replace("+","\+")+"'.*?)</div>"
    data_enlaces = scrapertools.find_single_match(data,patron)
    patron = 'dm\(c.a\(\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data_enlaces, patron)
    numero = len(matches)
    for code in matches:
        titulo = item.title.split("-")[0]+" - Enlace "+str(numero)
        numero -= 1
        enlace = dm(code)
        enlaces = servertools.findvideos(data=enlace)
        if len(enlaces)> 0:
            itemlist.append( Item(channel=__channel__, action="play", server=enlaces[0][2], title=titulo , url=enlaces[0][1] , fulltitle = item.fulltitle, thumbnail=item.thumbnail , fanart=item.fanart, plot=item.plot, folder=False) )
    itemlist.sort(key=lambda item: item.title)
    return itemlist

def dm(h):
    import base64
    h = base64.decodestring(h)

    copies = ""
    i = 0
    while i < len(h):
        copies += chr(ord(h[i]) ^ 123 * ~~ True)
        i += 1

    return copies
	

def info(title, type, sinopsis):
    logger.info("pelisalacarta.descargasmix info")
    infolabels={}
    plot={}
    try:
        from core.tmdb import Tmdb
        otmdb= Tmdb(texto_buscado=title, tipo= type)
        if otmdb.get_sinopsis() == "": infolabels['plot'] = sinopsis
        else: infolabels['plot'] = otmdb.get_sinopsis()
        infolabels['year']= otmdb.result["release_date"][:4]
        infolabels['genre'] = otmdb.get_generos()
        infolabels['rating'] = float(otmdb.result["vote_average"])
        fanart=otmdb.get_backdrop()
        plot['infoLabels']=infolabels
        return plot, fanart
    except:
        pass

def infoepi(otmdb, episode):
    logger.info("pelisalacarta.descargasmix infoepi")
    infolabels={}
    plot={}
    try:
        infolabels['season'] = episode.split("x")[0]
        infolabels['episode'] = episode.split("x")[1]
        episodio = otmdb.get_episodio(infolabels['season'], infolabels['episode'])
        if episodio["episodio_sinopsis"] == "": infolabels['plot'] = otmdb.get_sinopsis()
        else: infolabels['plot'] = episodio["episodio_sinopsis"]
        if episodio["episodio_titulo"] != "": infolabels['title'] =  episodio["episodio_titulo"]
        infolabels['year']= otmdb.result["release_date"][:4]
        infolabels['genre'] = otmdb.get_generos()
        infolabels['rating'] = float(otmdb.result["vote_average"])
        fanart=otmdb.get_backdrop()
        if episodio["episodio_imagen"] == "": thumbnail = otmdb.get_poster()
        else: thumbnail = episodio["episodio_imagen"]
        plot['infoLabels']=infolabels
        return plot, fanart, thumbnail
    except:
        pass