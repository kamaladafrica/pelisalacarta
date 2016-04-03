# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para oranline
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import urlparse
import re
import sys

from core import logger
from core import config
from core import scrapertools
from core import channeltools
from core import tmdb
from core.item import Item
from servers import servertools

__channel__ = "oranline"
__category__ = "F"
__type__ = "generic"
__title__ = "oranline"
__language__ = "ES"

#Pasar a configuracion del canal
__modo_grafico__ = True 
__perfil__= 0


DEBUG = config.get_setting("debug")

host = "http://www.oranline.com/"
b_idioma = {'1.png': 'ES', '2.png': 'LAT', '3.png': 'VOS', '4.png': 'VO', 's.png': 'ESP', 'l.png': 'LAT', 'i.png':
            'ING', 'v.png': 'VOSE'}

# Fijar perfil de color            
perfil = [['0xFFFFE6CC','0xFFFFCE9C','0xFF994D00'],
          ['0xFFA5F6AF','0xFF5FDA6D','0xFF11811E'],
          ['0xFF58D3F7','0xFF2E64FE','0xFF0404B4']]     
color1, color2, color3 = perfil[__perfil__]

parameters= channeltools.get_channel_parameters(__channel__)
fanart= parameters['fanart']
thumbnail_host= parameters['thumbnail']
  
            
def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.oranline mainlist")

    itemlist = list([])

    itemlist.append(Item(channel=__channel__, title="Películas", text_color= color2, fanart= fanart, folder= False
                            ,thumbnail= thumbnail_host, text_blod=True))
    url = urlparse.urljoin(host, "Pel%C3%ADculas/peliculas/")
    itemlist.append(Item(channel=__channel__, action="peliculas", title="      Novedades",
                         text_color= color1, fanart= fanart, url= url,
                         thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Directors%20Chair.png"))
    itemlist.append(Item(channel=__channel__, action="generos", title="      Filtradas por géneros",
                         text_color= color1, fanart= fanart, url=url,
                         thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Genre.png"))
    itemlist.append(Item(channel=__channel__, action="idiomas", title="      Filtradas por idioma",
                         text_color= color1, fanart= fanart, url=url,
                         thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Language.png"))
    url = urlparse.urljoin(host, "Pel%C3%ADculas/documentales/")
    itemlist.append(Item(channel=__channel__, title="Documentales", text_blod=True,
                         text_color= color2, fanart= fanart,thumbnail= thumbnail_host, folder= False))
    itemlist.append(Item(channel=__channel__, action="peliculas", title="      Novedades",
                         text_color= color1, fanart= fanart, url=url,
                         thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Documentaries.png"))
    url = urlparse.urljoin(host, "Pel%C3%ADculas/documentales/?orderby=title&order=asc&gdsr_order=asc")
    itemlist.append(Item(channel=__channel__, action="peliculas", title="      Por orden alfabético",
                         text_color= color1, fanart= fanart, url=url,
                         thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/A-Z.png"))
    itemlist.append(Item(channel=__channel__, title="", fanart= fanart, folder= False,thumbnail= thumbnail_host))                     
    itemlist.append(Item(channel=__channel__, action="search", title="Buscar...", text_color= color3, fanart= fanart,
                         thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Search.png"))
    url = urlparse.urljoin(host, "Pel%C3%ADculas/peliculas/")
    itemlist.append(Item(channel=__channel__, action="letras", title="Buscar por orden alfabético",
                         text_color= color3, fanart= fanart, url=url,
                         thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/A-Z.png"))

    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.channels.oranline search")
    if item.url == "":
        item.url = "http://www.oranline.com/?s="
    texto = texto.replace(" ", "+")
    item.url = item.url+texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%{0}".format(line))
        return []


def peliculas(item):
    logger.info("pelisalacarta.channels.oranline peliculas")
    itemlist = []

    # Descarga la página
    data = get_main_page(item.url)

    # Extrae las entradas (carpetas)
    patron = '<div class="review-box.*?'
    patron += '<a href="([^"]+)" title="([^"]+)"[^<]+'
    patron += '<img src="([^"]+)"[^<]+'
    patron += '</a[^<]+'
    patron += '<div id="mejor_calidad"[^<]+'
    patron += '<a[^<]+<img[^<]+'
    patron += '</a[^<]+'
    patron += '<span>([^<]+)</span></div[^<]+'
    patron += '</div[^<]+'
    patron += '<![^<]+'
    patron += '<div class="review-box-text"[^<]+'
    patron += '<h2[^<]+<a[^<]+</a></h2[^<]+'
    patron += '<p>([^<]+)</p[^<]+'
    patron += '</div[^<]+'
    patron += '<div id="campos_idiomas">(.*?)</div>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle, scrapedthumbnail, calidad, scrapedplot, scrapedidiomas in matches:
        scrapedtitle = scrapedtitle.replace("Ver Online Y Descargar Gratis", "").strip()
        scrapedtitle = scrapedtitle.replace("Ver Online Y Descargar gratis", "").strip()
        scrapedtitle = scrapedtitle.replace("Ver Online Y Descargar", "").strip()
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)

        year=  scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
        fulltitle= scrapedtitle.split('(')[0].strip()
        
        _idiomas_ = ""

        for key, value in b_idioma.iteritems():
            if key in scrapedidiomas:
                _idiomas_ += value + ", "
        if _idiomas_ != "":
            _idiomas_ = _idiomas_[:-2]

        title = "{0} ({1}) ({2})".format(scrapedtitle, calidad, _idiomas_)
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        plot = scrapedplot.strip()
        if DEBUG:
            logger.info("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, url, thumbnail))
        
        newItem = Item(channel=__channel__, action="findvideos", title=title, url=url, thumbnail=thumbnail,text_color= color1,
                             plot=plot, viewmode="movies_with_plot", folder=True, fulltitle=fulltitle, fanart=fanart)
        if unicode(year).isnumeric(): newItem.infoLabels['year']= int(year)

        itemlist.append(newItem)

    # Obtenemos los datos basicos de todas las peliculas mediante multihilos
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    try:
        next_page = scrapertools.get_match(data, "<a href='([^']+)'>\&rsaquo\;</a>")
        itemlist.append(Item(channel=__channel__, action="peliculas", title=">> Página siguiente",text_color= color3,
                             url=urlparse.urljoin(item.url, next_page), folder=True, fanart=fanart,thumbnail= thumbnail_host))
    except:
        try:
            next_page = scrapertools.get_match(data, "<span class='current'>\d+</span><a href='([^']+)'")
            itemlist.append(Item(channel=__channel__, action="peliculas", title=">> Página siguiente",text_color= color3,
                                 url=urlparse.urljoin(item.url, next_page), folder=True, fanart=fanart,thumbnail= thumbnail_host))
        except:
            pass
        pass
    
    
    
    return itemlist


def letras(item):
    logger.info("pelisalacarta.channels.oranline letras")
    itemlist = []

    # Descarga la página
    data = get_main_page(item.url)
    data = scrapertools.get_match(data, '<div id="alphaList" align="center">(.*?)</div>')

    # Extrae las entradas
    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/A-Z.png"
    
    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = urlparse.urljoin(item.url, scrapedurl)

        if DEBUG:
            logger.info("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, url, thumbnail))
        itemlist.append(Item(channel=__channel__, action="peliculas", title=title, url=url, thumbnail=thumbnail,
                             folder=True, text_color= color2, fanart=fanart))
    return itemlist


def generos(item):
    logger.info("pelisalacarta.channels.oranline generos")
    itemlist = []

    # Descarga la página
    data = get_main_page(item.url)
    # <li class="cat-item cat-item-23831"><a href="http://www.oranline.com/Películas/3d-hou/"
    # title="Ver todas las entradas archivadas en 3D-HOU">3D-HOU</a> (5)
    data = scrapertools.get_match(data, '<li class="cat-item cat-item-\d+"><a href="http://www.oranline.com/Pel.*?s'
                                        '/generos/"[^<]+</a>(.*?)</ul>')

    # Extrae las entradas
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)"[^>]*>([^<]+)<.*?\s+\(([^\)]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Genre.png"
    
    for scrapedurl, scrapedtitle, cuantas in matches:
        title = scrapedtitle.strip()+" ("+cuantas+")"
        url = urlparse.urljoin(item.url, scrapedurl)
        
        if DEBUG:
            logger.info("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, url, thumbnail))
        itemlist.append(Item(channel=__channel__, action="peliculas", title=title, url=url, thumbnail=thumbnail,
                             folder=True, text_color= color2, fanart=fanart))
    return itemlist


def idiomas(item):
    logger.info("pelisalacarta.channels.oranline idiomas")
    itemlist = []

    # Descarga la página
    data = get_main_page(item.url)
    data = scrapertools.get_match(data, '<div class="widget"><h3>&Uacute;ltimos estrenos</h3>(.*?)</ul>')

    # Extrae las entradas
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)"[^>]*>([^<]+)<.*?\s+\(([^\)]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    thumbnail= "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Language.png" 

    for scrapedurl, scrapedtitle, cuantas in matches:
        title = scrapedtitle.strip()+" ("+cuantas+")"
        url = urlparse.urljoin(item.url, scrapedurl)
        
        if DEBUG:
            logger.info("title=[{0}], url=[{1}]".format(title, url))
        itemlist.append(Item(channel=__channel__, action="peliculas", title=title, url=url, 
                             text_color= color2, folder=True, fanart=fanart, thumbnail=thumbnail))
    return itemlist


def get_main_page(url):
    logger.info("pelisalacarta.channels.oranline get_main_page")

    headers = list([])
    headers.append(["User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:20.0) Gecko/20100101 Firefox/20.0"])
    headers.append(["Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"])
    headers.append(["Accept-Language", "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"])
    headers.append(["Accept-Encoding", "gzip, deflate"])

    # Descarga la página
    data = scrapertools.cachePage(url, headers=headers)
    #logger.info("pelisalacarta.channels.oranline data="+data)

    return data


def findvideos(item):
    logger.info("pelisalacarta.channels.oranline findvideos")
    itemlist = []
    list =[]
    
    # Ampliamos datos en tmdb
    tmdb.set_infoLabels(item, __modo_grafico__)
    
    def finvideos_by_Category(item, data_0):
        list_0 =[]
        patron_0 = '<p>.*?<span>.*?<img.*?src="(.*?)".*?></span>.*?<span>(.*?)</span>.*?href=.*?href="(.*?)".*?src="(.*?)"'
        matches2 = re.compile(patron_0, re.DOTALL).findall(data_0)
        #scrapertools.printMatches(matches2)
        for img_idioma, calidad, scrapedurl, img_servidor in matches2:
            idioma = scrapertools.get_filename_from_url(img_idioma)
            if idioma in b_idioma.keys():
                idioma = b_idioma[idioma]
            servidor = scrapertools.get_filename_from_url(img_servidor)[:-4]
            title = "Mirror en "+servidor+" ("+idioma+") (Calidad "+calidad.strip()+")"
            url = urlparse.urljoin(item.url, scrapedurl)            
            if DEBUG:
                logger.info("title=[{0}], url=[{1}]".format(title, url))  
            newItem = item.clone(action="play", title=title, url=url, folder=True, text_color= color1)
            list_0.append(newItem)
        return list_0
    
    data = scrapertools.cache_page(item.url)
    patron = '<div id="veronline">(.*?)</form>'
    list = finvideos_by_Category(item,scrapertools.find_single_match(data,patron))
    if len(list) > 0:
        list.insert(0,Item(channel=__channel__, title="Ver online", text_color= color2, fanart= fanart, folder= False
                                ,thumbnail= thumbnail_host, text_blod=True))           
        itemlist.extend(list)
    
    patron = '<div id="descarga">(.*?)</form>'
    list = finvideos_by_Category(item,scrapertools.find_single_match(data,patron))
    if len(list) > 0:
        list.insert(0,Item(channel=__channel__, title="Descargar", text_color= color2, fanart= fanart, folder= False
                                ,thumbnail= thumbnail_host, text_blod=True))
        itemlist.extend(list)
    
    return itemlist


def play(item):
    logger.info("pelisalacarta.channels.oranline play")

    data2 = scrapertools.cache_page(item.url)
    logger.info("pelisalacarta.channels.oranline data2="+data2)

    itemlist = servertools.find_video_items(data=data2)
    
    return itemlist    


# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
'''def test():
    from servers import servertools
    
    # mainlist es "peliculas | documentales"
    mainlist_items = mainlist(Item())

    # peliculas es "novedades | alfabetco | generos | idiomas"
    peliculas_items = peliculas(mainlist_items[0])

    # novedades es la lista de pelis
    novedades_items = novedades(peliculas_items[0])
    bien = False
    for novedad_item in novedades_items:
        # mirrors es una lista de alternativas
        mirrors_items = mirrors(novedad_item)

        for mirror_item in mirrors_items:
            # videos con "play"
            videos = findvideos(mirror_item)
            for video in videos:
                enlaces = play(video)
                if len(enlaces) > 0:
                    return True

    return False'''
