# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canale per http://www.serietvu.com/
# http://www.mimediacenter.info/foro/viewforum.php?f=36
# By MrTruth
# ------------------------------------------------------------

import re

from core import config
from core import logger, httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core.tmdb import infoSod

__channel__ = "serietvu"

host = "http://www.serietvu.com"

headers = [['Referer', host]]


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info("[SerieTVU.py]==> mainlist")
    itemlist = [Item(channel=__channel__,
                     action="lista_serie",
                     title=color("Nuove serie TV", "orange"),
                     url="%s/category/serie-tv" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     action="latestep",
                     title=color("Nuovi Episodi", "azure"),
                     url="%s/ultimi-episodi" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     action="lista_serie",
                     title=color("Serie TV Aggiornate", "azure"),
                     url="%s/ultimi-episodi" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     action="categorie",
                     title=color("Categorie", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     action="search",
                     title=color("Cerca ...", "yellow"),
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info("[SerieTVU.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = "http://www.serietvu.com/ultimi-episodi"
            item.action = "latestep"
            itemlist = latestep(item)

            if itemlist[-1].action == "latestep":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info("[SerieTVU.py]==> search")
    item.url = host + "/?s=" + texto
    try:
        return lista_serie(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    logger.info("[SerieTVU.py]==> categorie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.get_match(data, r'<h2>Sfoglia</h2>\s*<ul>(.*?)</ul>\s*</section>')
    patron = r'<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=__channel__,
                 action="lista_serie",
                 title=scrapedtitle,
                 contentType="tv",
                 url="%s%s" % (host, scrapedurl),
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def latestep(item):
    logger.info("[SerieTVU.py]==> latestep")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div class="item">\s*<a href="([^"]+)" data-original="([^"]+)" class="lazy inner">'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<small>([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedimg, scrapedtitle, scrapedinfo in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
        episodio = re.compile(r'(\d+)x(\d+)', re.DOTALL).findall(scrapedinfo)
        title = "%s %s" % (scrapedtitle, scrapedinfo)
        itemlist.append(infoSod(
            Item(channel=__channel__,
                 action="findepisodevideo",
                 title=title,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 extra=episodio,
                 thumbnail=scrapedimg,
                 show=title,
                 folder=True), tipo="tv"))
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_serie(item):
    logger.info("[SerieTVU.py]==> lista_serie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div class="item">\s*<a href="([^"]+)" data-original="([^"]+)" class="lazy inner">'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedimg, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
        itemlist.append(infoSod(
            Item(channel=__channel__,
                 action="episodios",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedimg,
                 show=scrapedtitle,
                 folder=True), tipo="tv"))

    # Pagine
    patron = '<a href="([^"]+)"[^>]+>Pagina'
    next_page = scrapertools.find_single_match(data, patron)
    if len(matches) > 0:
        itemlist.append(
            Item(channel=__channel__,
                 action="HomePage",
                 title="[COLOR yellow]Torna Home[/COLOR]",
                 folder=True)),
        itemlist.append(
            Item(channel=__channel__,
                 action="lista_serie",
                 title="[COLOR orange]Successivo >>[/COLOR]",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodios(item):
    logger.info("[SerieTVU.py]==> episodios")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<option value="(\d+)"[\sselected]*>.*?</option>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for value in matches:
        patron = r'<div class="list [active]*" data-id="%s">(.*?)</div>\s*</div>' % value
        blocco = scrapertools.find_single_match(data, patron)

        patron = r'(<a data-id="\d+[^"]*" data-href="([^"]+)" data-original="([^"]+)" class="[^"]+">)[^>]+>[^>]+>([^<]+)</div>'
        matches = re.compile(patron, re.DOTALL).findall(blocco)
        for scrapedextra, scrapedurl, scrapedimg, scrapedtitle in matches:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.replace("Episodio", "")).strip()
            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     title=value + "x" + scrapedtitle.zfill(2),
                     fulltitle=scrapedtitle,
                     contentType="episode",
                     url=scrapedurl,
                     thumbnail=scrapedimg,
                     extra=scrapedextra,
                     folder=True))

    if config.get_library_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=__channel__,
                 title="Aggiungi alla libreria",
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))
        itemlist.append(
            Item(channel=__channel__,
                 title="Scarica tutti gli episodi della serie",
                 url=item.url,
                 action="download_all_episodes",
                 extra="episodios",
                 show=item.show))
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info("[SerieTVU.py]==> findvideos")
    itemlist = servertools.find_video_items(data=item.extra)

    try:
        # Non sono riuscito a trovare un modo migliore di questo, se qualcuno ha un metodo migliore di questo
        # per estrarre il video lo sistemi per favore.
        if len(itemlist) > 1:
            itemlist.remove(itemlist[1])
        server = re.sub(r'[-\[\]\s]+', '', itemlist[0].title)
        itemlist[0].title = "".join(["[%s] " % color(server, 'orange'), item.title])
        itemlist[0].fulltitle = item.fulltitle
        itemlist[0].show = item.show
        itemlist[0].thumbnail = item.thumbnail
        itemlist[0].channel = __channel__
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findepisodevideo(item):
    logger.info("[SerieTVU.py]==> findepisodevideo")

    try:
        # Download Pagina
        data = httptools.downloadpage(item.url, headers=headers).data

        # Prendo il blocco specifico per la stagione richiesta
        patron = r'<div class="list [active]*" data-id="%s">(.*?)</div>\s*</div>' % item.extra[0][0]
        blocco = scrapertools.find_single_match(data, patron)

        # Estraggo l'episodio
        patron = r'<a data-id="%s[^"]*" data-href="([^"]+)" data-original="([^"]+)" class="[^"]+">' % item.extra[0][
            1].lstrip("0")
        matches = re.compile(patron, re.DOTALL).findall(blocco)

        itemlist = servertools.find_video_items(data=matches[0][0])

        # Non sono riuscito a trovare un modo migliore di questo, se qualcuno ha un metodo migliore di questo
        # per estrarre il video lo sistemi per favore.
        if len(itemlist) > 1:
            itemlist.remove(itemlist[1])
        server = re.sub(r'[-\[\]\s]+', '', itemlist[0].title)
        itemlist[0].title = "".join(["[%s] " % color(server, 'orange'), item.title])
        itemlist[0].fulltitle = item.fulltitle
        itemlist[0].show = item.show
        itemlist[0].thumbnail = matches[0][1]
        itemlist[0].channel = __channel__
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def HomePage(item):
    import xbmc
    xbmc.executebuiltin("ReplaceWindow(10024,plugin://plugin.video.streamondemand/)")


def color(text, color):
    return "[COLOR " + color + "]" + text + "[/COLOR]"

# ================================================================================================================
