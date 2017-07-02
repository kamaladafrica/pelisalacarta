# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para itafilmtv
# http://blog.tvalacarta.info/plugin-xbmc/streamondemand.
#  By Costaplus
# ------------------------------------------------------------
import re
import urlparse

import xbmc
import xbmcgui

from core import config, httptools
from core import logger
from core import scrapertools
from core.item import Item
from core.tmdb import infoSod

__channel__ = "leserietv"

host = 'http://www.guardareserie.tv'

headers = [['Referer', host]]


# -----------------------------------------------------------------
def mainlist(item):
    logger.info("[leserietv.py] mainlist")
    itemlist = [Item(channel=__channel__,
                     action="novita",
                     title="[COLOR yellow]Novità[/COLOR]",
                     url=("%s/streaming/" % host),
                     thumbnail="http://www.ilmioprofessionista.it/wp-content/uploads/2015/04/TVSeries3.png",
                     fanart=FilmFanart),
                Item(channel=__channel__,
                     action="lista_serie",
                     title="[COLOR azure]Tutte le serie[/COLOR]",
                     url=("%s/streaming/" % host),
                     thumbnail="http://www.ilmioprofessionista.it/wp-content/uploads/2015/04/TVSeries3.png",
                     fanart=FilmFanart),
                Item(channel=__channel__,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="https://farm8.staticflickr.com/7562/15516589868_13689936d0_o.png",
                     fanart=FilmFanart),
                Item(channel=__channel__,
                     action="top50",
                     title="[COLOR azure]Top 50[/COLOR]",
                     url=("%s/top50.html" % host),
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     fanart=FilmFanart),
                Item(channel=__channel__,
                     extra="serie",
                     action="search",
                     title="[COLOR orange]Cerca...[/COLOR][I](minimo 3 caratteri)[/I]",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search",
                     fanart=FilmFanart),
                Item(channel=__channel__,
                     action="info",
                     title="[COLOR lime][I]Info canale[/I][/COLOR] [COLOR yellow]18/06/2017[/COLOR]",
                     thumbnail="http://www.mimediacenter.info/wp-content/uploads/2016/01/newlogo-final.png")]

    return itemlist


# =================================================================


# -----------------------------------------------------------------
def novita(item):
    logger.info("streamondemand.laserietv novità")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<div class="video-item-cover"[^<]+<a href="(.*?)">[^<]+<img src="(.*?)" alt="(.*?)">'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedthumbnail = host + scrapedthumbnail
        logger.info("title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")
        itemlist.append(infoSod(
            Item(channel=__channel__,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle, viewmode="movie"), tipo='tv'))

    # Paginazione
    # ===========================================================
    patron = '<div class="pages">(.*?)</div>'
    paginazione = scrapertools.find_single_match(data, patron)
    patron = '<span>.*?</span>.*?href="([^"]+)".*?</a>'
    matches = re.compile(patron, re.DOTALL).findall(paginazione)
    scrapertools.printMatches(matches)
    # ===========================================================

    if len(matches) > 0:
        paginaurl = matches[0]
        itemlist.append(
            Item(channel=__channel__, action="novita", title="[COLOR orange]Successivo>>[/COLOR]", url=paginaurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))
        itemlist.append(
            Item(channel=__channel__, action="HomePage", title="[COLOR yellow]Torna Home[/COLOR]",
                 thumbnail=ThumbnailHome, folder=True))
    return itemlist


# =================================================================

# -----------------------------------------------------------------
def lista_serie(item):
    logger.info("[leserie.py] lista_serie")
    itemlist = []

    post = "dlenewssortby=title&dledirection=asc&set_new_sort=dle_sort_cat&set_direction_sort=dle_direction_cat"

    data = httptools.downloadpage(item.url, post=post, headers=headers).data

    patron = '<div class="video-item-cover"[^<]+<a href="(.*?)">[^<]+<img src="(.*?)" alt="(.*?)">'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedthumbnail = host + scrapedthumbnail
        logger.info(scrapedurl + " " + scrapedtitle + scrapedthumbnail)
        itemlist.append(infoSod(
            Item(channel=__channel__,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle, viewmode="movie"), tipo='tv'))

    # Paginazione
    # ===========================================================
    patron = '<div class="pages">(.*?)</div>'
    paginazione = scrapertools.find_single_match(data, patron)
    patron = '<span>.*?</span>.*?href="([^"]+)".*?</a>'
    matches = re.compile(patron, re.DOTALL).findall(paginazione)
    scrapertools.printMatches(matches)
    # ===========================================================

    if len(matches) > 0:
        paginaurl = matches[0]
        itemlist.append(
            Item(channel=__channel__, action="lista_serie", title="[COLOR orange]Successivo>>[/COLOR]", url=paginaurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))
        itemlist.append(
            Item(channel=__channel__, action="HomePage", title="[COLOR yellow]Torna Home[/COLOR]",
                 thumbnail=ThumbnailHome, folder=True))
    return itemlist


# =================================================================

# -----------------------------------------------------------------
def categorias(item):
    logger.info("streamondemand.laserietv categorias")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.get_match(data, '<ul class="dropdown-menu cat-menu">(.*?)</ul>')

    # The categories are the options for the combo
    patron = '<li ><a href="([^"]+)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedurl = urlparse.urljoin(item.url, scrapedurl)
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=__channel__,
                 action="lista_serie",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot))

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def search(item, texto):
    logger.info("[laserietv.py] " + host + " search " + texto)

    itemlist = []

    post = "do=search&subaction=search&story=" + texto
    data = httptools.downloadpage("http://www.guardareserie.tv", post=post, headers=headers).data

    patron = '<div class="video-item-cover"[^<]+<a href="(.*?)">[^<]+<img src="(.*?)" alt="(.*?)">'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedthumbnail = host + scrapedthumbnail
        logger.info(scrapedurl + " " + scrapedtitle + scrapedthumbnail)
        itemlist.append(infoSod(
            Item(channel=__channel__,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle), tipo='tv'))

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def top50(item):
    logger.info("[laserietv.py] top50")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = 'class="top50item">\s*<[^>]+>\s*<.*?="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        scrapedthumbnail = ""
        logger.debug(scrapedurl + " " + scrapedtitle)
        itemlist.append(infoSod(
            Item(channel=__channel__,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle, viewmode="movie"), tipo='tv'))

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def episodios(item):
    logger.info("[leserietv.py] episodios")
    itemlist = []
    elenco = []
    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<li id[^<]+<[^<]+<.*?class="serie-title">(.*?)</span>[^>]+>[^<]+<.*?megadrive-(.*?)".*?data-link="([^"]+)">Megadrive</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedlongtitle, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.split('_')[0] + "x" + scrapedtitle.split('_')[1].zfill(2)

        elenco.append([scrapedtitle, scrapedlongtitle, scrapedurl])

        scrapedtitle = scrapedtitle + " [COLOR orange]" + scrapedlongtitle + "[/COLOR]"
        itemlist.append(Item(channel=__channel__,
                             action="findvideos",
                             title=scrapedtitle,
                             fulltitle=scrapedtitle,
                             url=scrapedurl,
                             thumbnail=item.thumbnail,
                             fanart=item.fanart if item.fanart != "" else item.scrapedthumbnail,
                             show=item.fulltitle))

    if config.get_library_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=__channel__,
                 title="Aggiungi alla libreria",
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 contentType="episode",
                 show=item.show))

    return itemlist


# =================================================================

# ------------------------------------------------------------------
def findvideos(item):
    itemlist = []

    item.url = item.url.replace(".tv", ".co")

    data = httptools.downloadpage(item.url, headers=headers).data

    elemento = scrapertools.find_single_match(data, 'file: "(.*?)",')

    itemlist.append(Item(channel=__channel__,
                         action="play",
                         title=item.title,
                         url=elemento,
                         thumbnail=item.thumbnail,
                         fanart=item.fanart,
                         fulltitle=item.fulltitle,
                         show=item.fulltitle))
    return itemlist


# =================================================================

# -----------------------------------------------------------------
def info(item):
    itemlist = []

    dialog = xbmcgui.Dialog()
    linea1 = '[COLOR yellow]Servizi ripristinati:[/COLOR]'
    linea2 = 'Link non funzionanti'
    linea3 = '\n[COLOR orange]www.mimediacenter.info[/COLOR] - [I]pelisalacarta (For Italian users)[/I]'

    result = dialog.ok('Le serie TV Info', linea1, linea2, linea3)

    return mainlist(itemlist)


# =================================================================
# -----------------------------------------------------------------
def HomePage(item):
    xbmc.executebuiltin("ReplaceWindow(10024,plugin://plugin.video.streamondemand)")


# =================================================================

FilmFanart = "https://superrepo.org/static/images/fanart/original/script.artwork.downloader.jpg"
ThumbnailHome = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Dynamic-blue-up.svg/580px-Dynamic-blue-up.svg.png"
