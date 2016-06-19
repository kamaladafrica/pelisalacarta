# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para oranline
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import sys
import urlparse

from core import channeltools
from core import config
from core import logger
from core import scrapertools
from core import servertools
from core import tmdb

from core.item import Item

__channel__ = "oranline"
__category__ = "F"
__type__ = "generic"
__title__ = "oranline"
__language__ = "ES"

# Configuracion del canal
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']]
color1, color2, color3 = perfil[__perfil__]

DEBUG = config.get_setting("debug")
host = "http://www.oranline.com/"
parameters = channeltools.get_channel_parameters(__channel__)
fanart = parameters['fanart']
thumbnail_host = parameters['thumbnail']
viewmode_options = {0: 'movie_with_plot', 1: 'movie', 2: 'list'}
viewmode = viewmode_options[config.get_setting('viewmode', __channel__)]


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.oranline mainlist")

    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Películas", text_color=color2, fanart=fanart, folder=False,
                         thumbnail=thumbnail_host, text_blod=True, viewmode=viewmode))
    itemlist.append(Item(channel=__channel__, action="peliculas", title="      Novedades",
                         text_color=color1, fanart=fanart, url=urlparse.urljoin(host, "ultimas-peliculas-online/"),
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Directors%20Chair.png"))

    itemlist.append(Item(channel=__channel__, action="peliculas", title="      Más vistas",
                         text_color=color1, fanart=fanart, url=urlparse.urljoin(host, "mas-visto/"),
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Favorites.png"))
    itemlist.append(Item(channel=__channel__, action="generos", title="      Filtradas por géneros",
                         text_color=color1, fanart=fanart, url=host,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Genre.png"))
    url = urlparse.urljoin(host, "category/documental/")
    itemlist.append(Item(channel=__channel__, title="Documentales", text_blod=True,
                         text_color=color2, fanart=fanart, thumbnail=thumbnail_host, folder=False))
    itemlist.append(Item(channel=__channel__, action="peliculas", title="      Novedades",
                         text_color=color1, fanart=fanart, url=url,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/Documentaries.png"))
    url = urlparse.urljoin(host, "category/documental/?orderby=title&order=asc&gdsr_order=asc")
    itemlist.append(Item(channel=__channel__, action="peliculas", title="      Por orden alfabético",
                         text_color=color1, fanart=fanart, url=url,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres/0/A-Z.png"))
    itemlist.append(Item(channel=__channel__, title="", fanart=fanart, folder=False, thumbnail=thumbnail_host))
    itemlist.append(Item(channel=__channel__, action="search", title="Buscar...", text_color=color3, fanart=fanart,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/oranline/buscar.png"))

    itemlist.append(Item(channel=__channel__, action="configuracion", title="Configurar canal...", text_color="gold",
                         thumbnail=thumbnail_host, fanart=fanart, folder=False))
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()


def search(item, texto):
    logger.info("pelisalacarta.channels.oranline search")
    item.url = "http://www.oranline.com/?s="
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%{0}".format(line))
        return []


def newest(categoria):
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = urlparse.urljoin(host, "ultimas-peliculas-online/")
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

        if categoria == 'documentales':
            item.url = urlparse.urljoin(host, "category/documental/")
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
    logger.info("pelisalacarta.channels.oranline peliculas")
    itemlist = []

    # Descarga la página
    data = scrapertools.downloadpage(item.url)

    # Extrae las entradas (carpetas)
    bloque = scrapertools.find_multiple_matches(data, '<li class="item">(.*?)</li>')
    for match in bloque:
        patron = 'href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)".*?' \
                 'div class="idiomas">(.*?)<div class="calidad">(.*?)</div>'
        matches = scrapertools.find_multiple_matches(match, patron)

        for scrapedurl, scrapedtitle, scrapedthumbnail, idiomas, calidad in matches:
            title = scrapedtitle + "  ["
            if '<div class="esp">' in idiomas:
                title += "ESP/"
            if '<div class="lat">' in idiomas:
                title += "LAT/"
            if '<div class="ing">' in idiomas:
                title += "ING/"
            if '<div class="vos">' in idiomas:
                title += "VOS/"
            if title[-1:] != "[":
                title = title[:-1] + "]"
            else:
                title = title[:-1]
            if "span" in calidad:
                calidad = scrapertools.find_single_match(calidad, '<span[^>]+>([^<]+)<')
                title += " (" + calidad.strip() + ")"

        if DEBUG:
            logger.info("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, scrapedurl, scrapedthumbnail))

        filtro_thumb = scrapedthumbnail.replace("http://image.tmdb.org/t/p/w185", "")
        filtro_list = {"poster_path": filtro_thumb}
        filtro_list = filtro_list.items()

        new_item = Item(channel=__channel__, action="findvideos", title=title, url=scrapedurl,
                        thumbnail=scrapedthumbnail, fulltitle=scrapedtitle, infoLabels={'filtro': filtro_list},
                        contentTitle=scrapedtitle, context="0", text_color=color1, viewmode=viewmode)
        itemlist.append(new_item)

    try:
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
    except:
        pass

    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page != "":
        itemlist.append(Item(channel=__channel__, action="peliculas", title=">> Página siguiente",
                             url=next_page.replace("&#038;", "&"), text_color=color3, folder=True))

    return itemlist


def generos(item):
    logger.info("pelisalacarta.channels.oranline generos")
    itemlist = []

    genres = {'Deporte': '3/Sports%20Film.jpg', 'Película de la televisión': '3/Tv%20Movie.jpg',
              'Estrenos de cine': '0/New%20Releases.png', 'Estrenos dvd y hd': '0/HDDVD%20Bluray.png'}
    # Descarga la página
    data = scrapertools.downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<div class="sub_title">Géneros</div>(.*?)</ul>')
    # Extrae las entradas
    patron = '<li><a href="([^"]+)".*?<i>(.*?)</i>.*?<b>(.*?)</b>'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    for scrapedurl, scrapedtitle, cuantas in matches:
        scrapedtitle = scrapedtitle.strip().capitalize()
        title = scrapedtitle + " (" + cuantas + ")"
        name_thumb = scrapertools.slugify(scrapedtitle)
        if scrapedtitle == "Foreign" or scrapedtitle == "Suspense" or scrapedtitle == "Thriller":
            thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/2/%s.jpg" \
                        % name_thumb.capitalize()
        elif scrapedtitle in genres:
            thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/%s" \
                        % genres[scrapedtitle]
        else:
            thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/1/%s.jpg" \
                        % name_thumb.replace("-", "%20")

        if DEBUG:
            logger.info("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, scrapedurl, thumbnail))
        itemlist.append(Item(channel=__channel__, action="peliculas", title=title, url=scrapedurl, thumbnail=thumbnail,
                             folder=True, text_color=color2, fanart=fanart, viewmode=viewmode))
    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.channels.oranline findvideos")
    itemlist = []

    try:
        filtro_idioma = config.get_setting("filterlanguages", __channel__)
        filtro_enlaces = config.get_setting("filterlinks", __channel__)
    except:
        filtro_idioma = 4
        filtro_enlaces = 2
    dict_idiomas = {'Español': 3, 'Latino': 2, 'VOSE': 1, 'Inglés': 0}

    data = scrapertools.downloadpage(item.url)
    year = scrapertools.find_single_match(data, 'Año de lanzamiento.*?href.*?>(\d+)</a>')

    if year != "":
        item.infoLabels['filtro'] = ""
        item.infoLabels['year'] = int(year)

    item.infoLabels['title'] = item.fulltitle
    # Ampliamos datos en tmdb
    try:
        tmdb.set_infoLabels(item, __modo_grafico__)
    except:
        pass

    if item.infoLabels['plot'] == "":
        plot = scrapertools.find_single_match(data, '<h2>Sinopsis</h2>.*?>(.*?)</p>')
        item.infoLabels['plot'] = plot

    if filtro_enlaces != 0:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "online", item)
        if list_enlaces:
            itemlist.append(item.clone(channel=__channel__, action="", title="Enlaces Online",
                                       text_color=color1, text_blod=True, viewmode="list", folder=False))
            itemlist.extend(list_enlaces)
    if filtro_enlaces != 1:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "descarga", item)
        if list_enlaces:
            itemlist.append(item.clone(channel=__channel__, action="", title="Enlaces Descarga",
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
    logger.info("pelisalacarta.channels.oranline bloque_enlaces")

    lista_enlaces = []
    bloque = scrapertools.find_single_match(data, '<div id="' + type + '">(.*?)</table>')
    patron = 'tr>[^<]+<td>.*?href="([^"]+)".*?<span>([^<]+)</span>' \
             '.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    filtrados = []
    for scrapedurl, server, language, calidad in matches:
        language = language.strip()
        server = server.lower()
        if server == "ul": server = "uploadedto"
        if server == "streamin": server = "streaminto"
        if server == "waaw": server = "netutv"
        mostrar_server = True
        if config.get_setting("hidepremium") == "true":
            mostrar_server = servertools.is_server_enabled(server)
        if mostrar_server:
            try:
                servers_module = __import__("servers." + server)
                title = "Mirror en " + server + " (" + language + ") (Calidad " + calidad.strip() + ")"
                if filtro_idioma == 4 or item.filtro:
                    lista_enlaces.append(item.clone(title=title, action="play", server=server, text_color=color2,
                                           url=scrapedurl, idioma=language, viewmode="list"))
                else:
                    idioma = dict_idiomas[language]
                    if idioma == filtro_idioma:
                        lista_enlaces.append(item.clone(title=title, text_color=color2, action="play",
                                    url=scrapedurl, server=server, viewmode="list"))
                    else:
                        if language not in filtrados: filtrados.append(language)
            except:
                pass

    if filtro_idioma != 4:
        if len(filtrados) > 0:
            title = "Mostrar enlaces filtrados en %s" % ", ".join(filtrados)
            lista_enlaces.append(item.clone(title=title, action="findvideos", url=item.url, text_color=color3,
                                   filtro=True, viewmode="list", folder=True))

    return lista_enlaces


def play(item):
    logger.info("pelisalacarta.channels.oranline play")
    itemlist = []
    enlace = servertools.findvideosbyserver(item.url, item.server)
    itemlist.append(item.clone(url=enlace[0][1]))

    return itemlist
