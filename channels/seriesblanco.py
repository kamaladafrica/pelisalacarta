# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import os
import re
import sys
import urlparse

from channelselector import get_thumbnail_path
from core import channeltools
from core import config
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item

from channels import filtertools


channel_xml = channeltools.get_channel_parameters("seriesblanco")
HOST = "http://seriesblanco.com/"
IDIOMAS = {'es': 'Español', 'en': 'Inglés', 'la': 'Latino', 'vo': 'VO', 'vos': 'VOS', 'vosi': 'VOSI', 'otro': 'OVOS'}
list_idiomas = [v for v in IDIOMAS.values()]
CALIDADES = ['SD', 'HDiTunes', 'Micro-HD-720p', 'Micro-HD-1080p', '1080p', '720p']

def mainlist(item):
    logger.info("[pelisalacarta.seriesblanco] mainlist")

    thumb_series = get_thumbnail("thumb_canales_series.png")
    thumb_series_az = get_thumbnail("thumb_canales_series_az.png")
    thumb_buscar = get_thumbnail("thumb_buscar.png")

    itemlist = list([])
    itemlist.append(Item(channel=item.channel, title="Series Listado Alfabetico", action="series_listado_alfabetico",
                         thumbnail=thumb_series_az))
    itemlist.append(Item(channel=item.channel, title="Todas las Series", action="series",
                         url=urlparse.urljoin(HOST, "listado/"), thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=HOST, thumbnail=thumb_buscar))

    if filtertools.context:
        itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, CALIDADES)

    return itemlist


def open_filtertools(item):
    return filtertools.mainlist_filter(channel=item.channel, list_idiomas=list_idiomas, list_calidad=CALIDADES)

def series(item):
    if not hasattr(item, 'extra') or not isinstance(item.extra, int):
        item.extra = 1

    pageURL = "{url}{merger}pagina={pageNo}".format(url = item.url, pageNo = item.extra, merger = '&' if '?' in item.url else '?')
    logger.info("[pelisalacarta.seriesblanco] series: {url}".format(url = pageURL))

    itemlist = []

    data = scrapertools.cache_page(pageURL)

    shows = re.findall("<li>[^<]*<[^<]*<a href=['\"](?P<url>[^'\"]+).*?<img.*?src='(?P<img>[^']+).*?title='(?P<name>[^']+)", data, re.MULTILINE | re.DOTALL)
    for url, img, name in shows:
        name = unicode(name, "iso-8859-1", errors="replace").encode("utf-8")
        logger.debug("[pelisalacarta.seriesblanco] Show found: {name} -> {url} ({img})".format(name = name, url = url, img = img))
        itemlist.append(Item(channel=item.channel, title=name, url=urlparse.urljoin(HOST, url),
                             action="episodios", show=name, thumbnail=img,
                             list_idiomas=list_idiomas, list_calidad=CALIDADES, context=filtertools.context))

    morePages = re.search('pagina=([0-9]+)">>>', data)
    if morePages:
        logger.debug("[pelisalacarta.seriesblanco] Adding next page item")
        itemlist.append(item.clone(title = "Siguiente >>", extra = item.extra + 1))

    if item.extra > 1:
        logger.debug("[pelisalacarta.seriesblanco] Adding previous page item")
        itemlist.append(item.clone(title = "<< Anterior", extra = item.extra - 1))

    return itemlist

def series_listado_alfabetico(item):
    logger.info("[pelisalacarta.seriesblanco] series_listado_alfabetico")

    return [item.clone(action="series", title=letra, url=urlparse.urljoin(HOST, "listado-{0}/".format(letra)))
                for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]

def search(item, texto):
    logger.info("[pelisalacarta.seriesblanco] search: {0}".format(texto))

    if texto == "":
        return []

    try:
        item.url = urlparse.urljoin(HOST, "/search.php?q1={0}&q2={1}".format(texto, texto.lower()))
        return series(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def episodios(item):
    logger.info("[pelisalacarta.seriesblanco] episodios: {0} - {1}".format(item.title, item.url))

    itemlist = []

    # Descarga la página
    data = scrapertools.cache_page(item.url)

    fanart = scrapertools.find_single_match(data, "background-image[^'\"]+['\"]([^'\"]+)")
    plot = scrapertools.find_single_match(data, "id=['\"]profile2['\"]>\s*(.*?)\s*</div>")

    logger.debug("[pelisalacarta.seriesblanco] fanart: {0}".format(fanart))
    logger.debug("[pelisalacarta.seriesblanco] plot: {0}".format(plot))


    episodes = re.findall("<tr.*?href=['\"](?P<url>[^'\"]+).+?>(?P<title>.+?)</a>.*?<td>(?P<flags>.*?)</td>", data, re.MULTILINE | re.DOTALL)
    for url, title, flags in episodes:
        idiomas = " ".join(["[{0}]".format(IDIOMAS.get(language, "OVOS")) for language in re.findall("banderas/([^\.]+)", flags, re.MULTILINE)])
        displayTitle = "{show} - {title} {languages}".format(show = item.show, title = title, languages = idiomas)
        logger.debug("[pelisalacarta.seriesblanco] Episode found {0}: {1}".format(displayTitle, urlparse.urljoin(HOST, url)))
        itemlist.append(item.clone(title=displayTitle, url=urlparse.urljoin(HOST, url),
                                   action="findvideos", plot=plot, fanart=fanart, language=idiomas,
                                   list_idiomas=list_idiomas, list_calidad=CALIDADES, context=filtertools.context))

    if len(itemlist) > 0 and filtertools.context:
        itemlist = filtertools.get_links(itemlist, item.channel)

    if config.get_library_support() and len(itemlist) > 0:
        itemlist.append(item.clone(title="Añadir esta serie a la biblioteca", action="add_serie_to_library", extra="episodios"))

    return itemlist


def parseVideos(item, typeStr, data):
    videoPatternsStr = [
        '<tr.+?<span>(?P<date>.+?)</span>.*?banderas/(?P<language>[^\.]+).+?href="(?P<link>[^"]+).+?servidores/'
        '(?P<server>[^\.]+).*?</td>.*?<td>.*?<span>(?P<uploader>.+?)</span>.*?<span>(?P<quality>.*?)</span>',
        '<tr.+?banderas/(?P<language>[^\.]+).+?<td[^>]*>(?P<date>.+?)</td>.+?href=[\'"](?P<link>[^\'"]+)'
        '.+?servidores/(?P<server>[^\.]+).*?</td>.*?<td[^>]*>.*?<a[^>]+>(?P<uploader>.+?)</a>.*?</td>.*?<td[^>]*>'
        '(?P<quality>.*?)</td>.*?</tr>'
    ]

    for vPatStr in videoPatternsStr:
        vPattIter = re.compile(vPatStr, re.MULTILINE | re.DOTALL).finditer(data)

        itemlist = []

        for vMatch in vPattIter:
            vFields = vMatch.groupdict()
            quality = vFields.get("quality")
            if not quality:
                quality = "SD"

            title = "{0} en {1} [{2}] [{3}] ({4}: {5})"\
                .format(typeStr, vFields.get("server"), IDIOMAS.get(vFields.get("language"), "OVOS"), quality,
                        vFields.get("uploader"), vFields.get("date"))
            itemlist.append(item.clone(title=title, fulltitle=item.title, url=urlparse.urljoin(HOST, vFields.get("link")),
                                       action="play", language=IDIOMAS.get(vFields.get("language"), "OVOS"),
                                       quality=quality, list_idiomas=list_idiomas, list_calidad=CALIDADES,
                                       context=filtertools.context))

        if len(itemlist) > 0 and filtertools.context:
            itemlist = filtertools.get_links(itemlist, item.channel)

        if len(itemlist) > 0:
            return itemlist

    return []


def extractVideosSection(data):
    return re.findall("panel-title(.+?)</div>[^<]*</div>[^<]*</div>", data, re.MULTILINE | re.DOTALL)


def findvideos(item):
    logger.info("[pelisalacarta.seriesblanco] findvideos: {0} = {1}".format(item.show, item.url))

    # Descarga la página
    data = scrapertools.cache_page(item.url)
    # logger.info(data)

    online = extractVideosSection(data)
    return parseVideos(item, "Ver", online[0]) + parseVideos(item, "Descargar", online[1])


def play(item):
    logger.info("[pelisalacarta.seriesblanco] play: {0} - {1} = {2}".format(item.show, item.title, item.url))

    if item.url.startswith(HOST):
        data = scrapertools.cache_page(item.url)

        patron = "<input type='button' value='Ver o Descargar' onclick='window.open\(\"([^\"]+)\"\);'/>"
        url = scrapertools.find_single_match(data, patron)
    else:
        url = item.url

    itemlist = servertools.find_video_items(data=url)

    titulo = scrapertools.find_single_match(item.fulltitle, "^(.*?)\s\[.+?$")
    if titulo:
        titulo += " [{language}]".format(language=item.language)

    for videoitem in itemlist:
        if titulo:
            videoitem.title = titulo
        else:
            videoitem.title = item.title
        videoitem.channel = item.channel

    return itemlist


def get_thumbnail(thumb_name=None):
    img_path = config.get_runtime_path() + '/resources/images/squares'
    if thumb_name:
        file_path = os.path.join(img_path, thumb_name)
        if os.path.isfile(file_path):
            thumb_path = file_path
        else:
            thumb_path = urlparse.urljoin(get_thumbnail_path(), thumb_name)
    else:
        thumb_path = urlparse.urljoin(get_thumbnail_path(), thumb_name)

    return thumb_path
