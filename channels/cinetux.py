# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinetux
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import urllib
import urlparse

from core import config
from core import httptools
from core import logger
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item


CHANNEL_HOST = "http://www.cinetux.net/"

# Configuracion del canal
__modo_grafico__ = config.get_setting('modo_grafico', 'cinetux')
__perfil__ = config.get_setting('perfil', 'cinetux')

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]
color1, color2, color3 = perfil[__perfil__]

fanart = "http://pelisalacarta.mimediacenter.info/fanart/cinetux.jpg"
viewmode_options = {0: 'movie_with_plot', 1: 'movie', 2: 'list'}
viewmode = viewmode_options[config.get_setting('viewmode', 'cinetux')]


def mainlist(item):
    logger.info()
    itemlist = []
    item.viewmode = viewmode
    item.fanart = fanart

    itemlist.append(item.clone(title="Películas", text_color=color2, action="", text_blod=True))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=CHANNEL_HOST + "pelicula",
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Directors%20Chair.png",
                               text_color=color1))
    itemlist.append(item.clone(action="vistas", title="      Más vistas", url="http://www.cinetux.net/mas-vistos/",
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Favorites.png",
                               text_color=color1))
    itemlist.append(item.clone(action="idioma", title="      Por idioma", text_color=color1))
    itemlist.append(item.clone(action="generos", title="      Por géneros", url=CHANNEL_HOST,
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Genre.png",
                               text_color=color1))

    url = urlparse.urljoin(CHANNEL_HOST, "genero/documental/")
    itemlist.append(item.clone(title="Documentales", text_blod=True, text_color=color2, action=""))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=url, text_color=color1,
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Documentaries.png"))
    url = urlparse.urljoin(CHANNEL_HOST, "genero/documental/?orderby=title&order=asc&gdsr_order=asc")
    itemlist.append(item.clone(action="peliculas", title="      Por orden alfabético", text_color=color1, url=url,
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/A-Z.png"))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(action="search", title="Buscar...", text_color=color3))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))

    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = "http://www.cinetux.net/?s="
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = CHANNEL_HOST
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

        elif categoria == 'documentales':
            item.url = urlparse.urljoin(CHANNEL_HOST, "genero/documental/")
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

        elif categoria == 'infantiles':
            item.url = urlparse.urljoin(CHANNEL_HOST, "genero/infantil/")
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    item.text_color = color2

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)class="(?:result-item|item movies)">.*?href="([^"]+)">'
    patron +='\s*<img src="([^"]+)'
    patron +='.*?alt="([^"]+)'
    patron +='(.*?)'
    patron +='(?:<span>|<span class="year">)([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, calidad, scrapedyear in matches:
        calidad = scrapertools.find_single_match(calidad, '.*?quality">([^<]+)')
        try:
            fulltitle = scrapedtitle
            year = scrapedyear
            if "/" in fulltitle:
                fulltitle = fulltitle.split(" /", 1)[0]
            scrapedtitle = "%s (%s)" % (fulltitle, year)
        except:
            fulltitle = scrapedtitle
        if calidad:
            scrapedtitle += "  [%s]" % calidad
        new_item = item.clone(action="findvideos", title=scrapedtitle, fulltitle=fulltitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentTitle=fulltitle, contentType="movie")
        if year:
            new_item.infoLabels['year'] = int(year)
        itemlist.append(new_item)
    try:
        #tmdb.set_infoLabels(itemlist, __modo_grafico__)
        a = 1
    except:
        pass

    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone(action="peliculas", title=">> Página siguiente", url=next_page_link,
                                   text_color=color3))

    return itemlist


def vistas(item):
    logger.info()
    itemlist = []
    item.text_color = color2

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    patron = '<li class="item">.*?href="([^"]+)".*?src="([^"]+)"' \
             '.*?<h3 class="name"><a.*?>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        new_item = item.clone(action="findvideos", title=scrapedtitle, fulltitle=scrapedtitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentTitle=scrapedtitle, contentType="movie")
        itemlist.append(new_item)

    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page_link:
        itemlist.append(item.clone(action="vistas", title=">> Página siguiente", url=next_page_link, text_color=color3))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '(?s)dos_columnas">(.*?)</ul>')
    # Extrae las entradas
    patron = '<li><a href="/([^"]+)">(.*?)</li>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        scrapedurl = CHANNEL_HOST + scrapedurl
        scrapedtitle = scrapertools.htmlclean(scrapedtitle).strip()
        scrapedtitle = unicode(scrapedtitle, "utf8").capitalize().encode("utf8")
        if scrapedtitle == "Erotico" and config.get_setting("adult_mode") == 0:
            continue

        itemlist.append(item.clone(action="peliculas", title=scrapedtitle, url=scrapedurl))

    return itemlist


def idioma(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(action="peliculas", title="Español", url="http://www.cinetux.net/idioma/espanol/"))
    itemlist.append(item.clone(action="peliculas", title="Latino", url="http://www.cinetux.net/idioma/latino/"))
    itemlist.append(item.clone(action="peliculas", title="VOSE", url="http://www.cinetux.net/idioma/subtitulado/"))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []

    try:
        filtro_idioma = config.get_setting("filterlanguages", item.channel)
        filtro_enlaces = config.get_setting("filterlinks", item.channel)
    except:
        filtro_idioma = 3
        filtro_enlaces = 2
    dict_idiomas = {'Español': 2, 'Latino': 1, 'Subtitulado': 0}

    # Busca el argumento
    data = httptools.downloadpage(item.url).data
    year = scrapertools.find_single_match(item.title, "\(([0-9]+)")

    if year and item.extra != "library":
        item.infoLabels['year'] = int(year)        
        # Ampliamos datos en tmdb
        if not item.infoLabels['plot']:
            try:
                tmdb.set_infoLabels(item, __modo_grafico__)
            except:
                pass

    if not item.infoLabels.get('plot'):
        plot = scrapertools.find_single_match(data, '<div class="sinopsis"><p>(.*?)</p>')
        item.infoLabels['plot'] = plot

    if filtro_enlaces != 0:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "online", item)
        if list_enlaces:
            itemlist.append(item.clone(action="", title="Enlaces Online", text_color=color1,
                                       text_blod=True))
            itemlist.extend(list_enlaces)
    if filtro_enlaces != 1:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "descarga", item)
        if list_enlaces:
            itemlist.append(item.clone(action="", title="Enlaces Descarga", text_color=color1,
                                       text_blod=True))
            itemlist.extend(list_enlaces)

    if itemlist:
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))    
        # Opción "Añadir esta película a la biblioteca de XBMC"
        if item.extra != "library":
            if config.get_library_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la biblioteca", text_color="green",
                                     filtro=True, action="add_pelicula_to_library", url=item.url,
                                     infoLabels={'title': item.fulltitle}, fulltitle=item.fulltitle,
                                     extra="library"))
    
    else:
        itemlist.append(item.clone(title="No hay enlaces disponibles", action="", text_color=color3))

    return itemlist


def bloque_enlaces(data, filtro_idioma, dict_idiomas, type, item):
    logger.info()
    lista_enlaces = []
    data = data.replace("\n","")
    matches = []
    if type == "online":
        patron = 'play-box-iframe.*?src.*?>([^<]+)<.*?<.*?src="([^"]+)'
        bloques = scrapertools.find_multiple_matches(data, patron)
        for language, url in bloques:
            if "goo.gl" in url:
                url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location","")
            server = servertools.get_server_from_url(url)
            matches.append([url, server, "", language, "online"])
    bloque2 = scrapertools.find_single_match(data, '(?s)box_links.*?dt_social_single')
    patron  = '(?s)optn" href="([^"]+)'
    patron += '.*?title="([^"]+)'
    patron += '.*?src.*?src="[^>]+"/>([^<]+)'
    patron += '.*?src[^>]+>([^<]+)'
    patron += '.*?</span>([^<]+)'
    matches.extend(scrapertools.find_multiple_matches(bloque2, patron))
    filtrados = []
    for match in matches:
        if type.upper() not in match[4].upper():
            continue
        scrapedurl = match[0]
        language = match[3]
        title = "   Mirror en " + match[1].split(".")[0] + " (" + language + ")"
        if len(match[2].strip()) > 0:
            title += " (Calidad " + match[2].strip() + ")"

        if filtro_idioma == 3 or item.filtro:
            lista_enlaces.append(item.clone(title=title, action="play", text_color=color2,
                                            url=scrapedurl, server=match[1], idioma=language, extra=item.url))
        else:
            idioma = dict_idiomas[language]
            if idioma == filtro_idioma:
                lista_enlaces.append(item.clone(title=title, text_color=color2, action="play",  url=scrapedurl,
                                                extra=item.url))
            else:
                if language not in filtrados:
                    filtrados.append(language)
    if filtro_idioma != 3:
        if len(filtrados) > 0:
            title = "Mostrar enlaces filtrados en %s" % ", ".join(filtrados)
            lista_enlaces.append(item.clone(title=title, action="findvideos", url=item.url, text_color=color3,
                                            filtro=True))
    return lista_enlaces


def play(item):
    logger.info()
    itemlist = []
    video_urls = []
    urls = []
    if "api.cinetux" in item.url:
        data = httptools.downloadpage(item.url, headers={'Referer': item.extra}).data.replace("\\", "")
        id = scrapertools.find_single_match(data, 'img src="[^#]+#(.*?)"')

        doc_url = "http://docs.google.com/get_video_info?docid=" + id
        response = httptools.downloadpage(doc_url, cookies=False)
        cookies = ""
        cookie = response.headers["set-cookie"].split("HttpOnly, ")
        for c in cookie:
            cookies += c.split(";", 1)[0] + "; "

        data = response.data.decode('unicode-escape')
        data = urllib.unquote_plus(urllib.unquote_plus(data))
        headers_string = "|Cookie=" + cookies

        url_streams = scrapertools.find_single_match(data, 'url_encoded_fmt_stream_map=(.*)')
        streams = scrapertools.find_multiple_matches(url_streams,
                                                 'itag=(\d+)&url=(.*?)(?:;.*?quality=.*?(?:,|&)|&quality=.*?(?:,|&))')

        itags = {'18':'360p', '22':'720p', '34':'360p', '35':'480p', '37':'1080p', '43':'360p', '59':'480p'}
        for itag, video_url in streams:
            if not video_url in urls:
                video_url += headers_string
                video_urls.append([video_url, itags[itag]])
                urls.append(video_url)
        
        video_urls.sort(key=lambda video_urls: int(video_urls[1].replace("p", "")))
        for v in video_urls:
            itemlist.append([v[1], v[0]])
    elif "links" in item.url:
        data = httptools.downloadpage(item.url).data
        scrapedurl = scrapertools.find_single_match(data, '<a href="(http[^"]+)')
        if scrapedurl == "":
            scrapedurl = scrapertools.find_single_match(data, '<frame src="(http[^"]+)')
        if "goo.gl" in scrapedurl:
            scrapedurl = httptools.downloadpage(scrapedurl, follow_redirects=False, only_headers=True).headers.get("location", "")
        item.url = scrapedurl
        item.server = servertools.get_server_from_url(scrapedurl)
        return [item]
    else:
        return [item]
    return itemlist
