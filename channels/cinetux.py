# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinetux
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import sys
import urlparse

from core import config
from core import logger
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item


CHANNEL_HOST = "http://www.cinetux.net/"
CHANNEL_DEFAULT_HEADERS = [
    ["User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0"],
    ["Accept-Encoding", "gzip, deflate"],
    ["Referer", CHANNEL_HOST]
]

# Configuracion del canal
try:
    __modo_grafico__ = config.get_setting('modo_grafico', 'cinetux')
    __perfil__ = int(config.get_setting('perfil', 'cinetux'))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']]
color1, color2, color3 = perfil[__perfil__]

DEBUG = config.get_setting("debug")
thumbnail_host = "http://media.tvalacarta.info/pelisalacarta/squares/cinetux.png"
fanart = "http://pelisalacarta.mimediacenter.info/fanart/cinetux.jpg"
viewmode_options = {0: 'movie_with_plot', 1: 'movie', 2: 'list'}
viewmode = viewmode_options[config.get_setting('viewmode', 'cinetux')]


def mainlist(item):
    logger.info("pelisalacarta.channels.cinetux mainlist")

    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Películas", text_color=color2, fanart=fanart, folder=False,
                         thumbnail=thumbnail_host, text_blod=True))
    itemlist.append(Item(channel=item.channel, action="peliculas", title="      Novedades", url=CHANNEL_HOST,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Directors%20Chair.png",
                         fanart=fanart, text_color=color1, viewmode=viewmode))
    itemlist.append(
        Item(channel=item.channel, action="vistas", title="      Más vistas", url="http://www.cinetux.net/mas-vistos/",
             thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Favorites.png",
             text_color=color1, fanart=fanart, viewmode=viewmode))
    itemlist.append(Item(channel=item.channel, action="generos", title="      Por géneros", url=CHANNEL_HOST,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Genre.png",
                         fanart=fanart, text_color=color1, viewmode=viewmode))

    url = urlparse.urljoin(CHANNEL_HOST, "genero/documental/")
    itemlist.append(Item(channel=item.channel, title="Documentales", text_blod=True,
                         text_color=color2, fanart=fanart, thumbnail=thumbnail_host, folder=False))
    itemlist.append(Item(channel=item.channel, action="peliculas", title="      Novedades", text_color=color1,
                         fanart=fanart, url=url,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Documentaries.png"))
    url = urlparse.urljoin(CHANNEL_HOST, "genero/documental/?orderby=title&order=asc&gdsr_order=asc")
    itemlist.append(Item(channel=item.channel, action="peliculas", title="      Por orden alfabético",
                         text_color=color1, fanart=fanart, url=url,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/A-Z.png"))
    itemlist.append(Item(channel=item.channel, title="", fanart=fanart, folder=False, thumbnail=thumbnail_host))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...", text_color=color3, fanart=fanart,
                         thumbnail=thumbnail_host))
    itemlist.append(
        Item(channel=item.channel, action="configuracion", thumbnail=thumbnail_host, title="Configurar canal...",
             text_color="gold", fanart=fanart, viewmode=viewmode, folder=False))
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()


def search(item, texto):
    logger.info("pelisalacarta.channels.cinetux search")
    if item.url == "":
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
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = CHANNEL_HOST
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

        if categoria == 'documentales':
            item.url = urlparse.urljoin(CHANNEL_HOST, "genero/documental/")
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
    logger.info("pelisalacarta.channels.cinetux peliculas")
    itemlist = []

    # Descarga la página
    data = scrapertools.anti_cloudflare(item.url, headers=CHANNEL_DEFAULT_HEADERS, host=CHANNEL_HOST)

    # Extrae las entradas (carpetas)
    patron = '<div class="item">.*?href="([^"]+)".*?src="([^"]+)"'
    patron += '.*?<h3 class="name"><a.*?>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        try:
            fulltitle, year = scrapedtitle.rsplit("(", 1)
            year = scrapertools.get_match(year, '(\d{4})')
        except:
            fulltitle = scrapedtitle
            year = ""
        if (DEBUG): logger.info(
            "title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")
        new_item = Item(channel=item.channel, action="findvideos", title=scrapedtitle, fulltitle=fulltitle,
                        url=scrapedurl, thumbnail=scrapedthumbnail,
                        fanart="http://pelisalacarta.mimediacenter.info/fanart/cinetux.jpg", infoLabels={},
                        contentTitle=fulltitle, context="0", text_color=color2, viewmode=viewmode, folder=True)
        if year != "": new_item.infoLabels['year'] = int(year)
        itemlist.append(new_item)
    try:
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
    except:
        pass

    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page_link != "":
        itemlist.append(Item(channel=item.channel, action="peliculas", title=">> Página siguiente", extra="next_page",
                             url=next_page_link, fanart="http://pelisalacarta.mimediacenter.info/fanart/cinetux.jpg",
                             folder=True))

    return itemlist


def vistas(item):
    logger.info("pelisalacarta.channels.cinetux vistas")
    itemlist = []

    # Descarga la página
    data = scrapertools.anti_cloudflare(item.url, headers=CHANNEL_DEFAULT_HEADERS, host=CHANNEL_HOST)

    # Extrae las entradas (carpetas)
    patron = '<li class="item">.*?href="([^"]+)".*?src="([^"]+)"'
    patron += '.*?<h3 class="name"><a.*?>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        if (DEBUG): logger.info(
            "title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")
        new_item = Item(channel=item.channel, action="findvideos", title=scrapedtitle, fulltitle=scrapedtitle,
                        url=scrapedurl, thumbnail=scrapedthumbnail, 
                        fanart="http://pelisalacarta.mimediacenter.info/fanart/cinetux.jpg", infoLabels={},
                        contentTitle=scrapedtitle, context="0", text_color=color2, viewmode=viewmode, folder=True)
        itemlist.append(new_item)

    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page_link != "":
        itemlist.append(Item(channel=item.channel, action="vistas", title=">> Página siguiente", extra="next_page",
                             url=next_page_link, fanart="http://pelisalacarta.mimediacenter.info/fanart/cinetux.jpg",
                             folder=True))

    return itemlist


def generos(item):
    logger.info("pelisalacarta.channels.cinetux generos")
    itemlist = []

    # Descarga la página
    data = scrapertools.downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<div class="sub_title">Géneros</div>(.*?)</ul>')
    # Extrae las entradas
    patron = '<li><a href="([^"]+)".*?<i>(.*?)</i>.*?<b>(.*?)</b>'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    for scrapedurl, scrapedtitle, cuantas in matches:
        scrapedtitle = scrapedtitle.strip().capitalize()
        if scrapedtitle == "Erotico" and not config.get_setting("adult_mode"): continue
        title = scrapedtitle + " (" + cuantas + ")"
        if DEBUG:
            logger.info("title=[{0}], url=[{1}]".format(title, scrapedurl))
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=title, url=scrapedurl, thumbnail=thumbnail_host,
                 folder=True))
    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.channels.cinetux findvideos")
    itemlist = []

    try:
        filtro_idioma = config.get_setting("filterlanguages", item.channel)
        filtro_enlaces = config.get_setting("filterlinks", item.channel)
    except:
        filtro_idioma = 3
        filtro_enlaces = 2
    dict_idiomas = {'Español': 2, 'Latino': 1, 'Subtitulado': 0}

    # Busca el argumento
    data = scrapertools.anti_cloudflare(item.url, headers=CHANNEL_DEFAULT_HEADERS, host=CHANNEL_HOST)
    year = scrapertools.find_single_match(data, '<h1><span>.*?rel="tag">([^<]+)</a>')

    if year != "":
        item.infoLabels['year'] = int(year)
    item.infoLabels['title'] = item.fulltitle
    # Ampliamos datos en tmdb
    try:
        tmdb.set_infoLabels(item, __modo_grafico__)
    except:
        pass

    if item.infoLabels['plot'] == "":
        plot = scrapertools.find_single_match(data, '<div class="sinopsis"><p>(.*?)</p>')
        item.infoLabels['plot'] = plot

    if filtro_enlaces != 0:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "online", item)
        if list_enlaces:
            itemlist.append(item.clone(channel=item.channel, action="", title="Enlaces Online",
                                       text_color=color1, text_blod=True, viewmode="list", folder=False))
            itemlist.extend(list_enlaces)
    if filtro_enlaces != 1:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "descarga", item)
        if list_enlaces:
            itemlist.append(item.clone(channel=item.channel, action="", title="Enlaces Descarga",
                                       text_color=color1, text_blod=True, viewmode="list", folder=False))
            itemlist.extend(list_enlaces)

    # Opción "Añadir esta película a la biblioteca de XBMC"
    if config.get_library_support() and item.category != "Cine" and itemlist:
        itemlist.append(item.clone(title="Añadir enlaces a la biblioteca", text_color="gold", viewmode="list",
                                   filtro=True, action="add_pelicula_to_library"))
    
    if not itemlist:
        itemlist.append(item.clone(title="No hay enlaces disponibles", action="", text_color=color3,
                                   viewmode="list", folder=False))

    return itemlist


def bloque_enlaces(data, filtro_idioma, dict_idiomas, type, item):
    logger.info("pelisalacarta.channels.cinetux bloque_enlaces")

    lista_enlaces = []

    matches = []
    if type == "online":
        patron = '<a href="#([^"]+)" data-toggle="tab">([^<]+)</a>'
        bloques = scrapertools.find_multiple_matches(data, patron)
        for id, language in bloques:
            patron = 'id="' + id + '">.*?<iframe src="([^"]+)"'
            url = scrapertools.find_single_match(data, patron)
            matches.append([url, "", language])

    bloque2 = scrapertools.find_single_match(data, '<div class="table-link" id="' + type + '">(.*?)</table>')
    patron = 'tr>[^<]+<td>.*?href="([^"]+)".*?src.*?title="([^"]+)"' \
             '.*?src.*?title="([^"]+)".*?src.*?title="([^"]+)"'
    matches.extend(scrapertools.find_multiple_matches(bloque2, patron))
    filtrados = []
    for match in matches:
        scrapedurl = match[0]
        language = match[2].strip()
        if match[1] == "":
            server = servertools.get_server_from_url(scrapedurl)
            title = "Mirror en " + server + " (" + language + ")"
        else:
            server = match[1].lower()
            if server == "uploaded": server = "uploadedto"
            if server == "streamin": server = "streaminto"
            if server == "netu": server = "netutv"
            mostrar_server = True
            if config.get_setting("hidepremium") == "true":
                mostrar_server = servertools.is_server_enabled(server)
            if mostrar_server:
                try:
                    servers_module = __import__("servers." + server)
                except:
                    pass
            title = "Mirror en " + server + " (" + language + ") (Calidad " + match[3].strip() + ")"

        if filtro_idioma == 3 or item.filtro:
            lista_enlaces.append(item.clone(title=title, action="play", server=server, text_color=color2, url=scrapedurl,
                                   idioma=language, viewmode="list"))
        else:
            idioma = dict_idiomas[language]
            if idioma == filtro_idioma:
                lista_enlaces.append(item.clone(title=title, text_color=color2, action="play",  url=scrapedurl, server=server,
                                       viewmode="list"))
            else:
                if language not in filtrados: filtrados.append(language)

    if filtro_idioma != 3:
        if len(filtrados) > 0:
            title = "Mostrar enlaces filtrados en %s" % ", ".join(filtrados)
            lista_enlaces.append(item.clone(title=title, action="findvideos", url=item.url, text_color=color3, filtro=True,
                                   viewmode="list", folder=True))

    return lista_enlaces


def play(item):
    logger.info("pelisalacarta.channels.cinetux play")
    itemlist = []
    enlace = servertools.findvideosbyserver(item.url, item.server)
    itemlist.append(item.clone(url=enlace[0][1]))

    return itemlist


# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    novedades_items = peliculas(mainlist_items[0])
    bien = False
    for novedades_item in novedades_items:
        mirrors = findvideos(item=novedades_item)
        if len(mirrors) > 0:
            bien = True
            break

    return bien
