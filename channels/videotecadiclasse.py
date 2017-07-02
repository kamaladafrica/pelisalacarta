# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# videotecadiclasse
# http://www.mimediacenter.info/foro/viewforum.php?f=36
# ------------------------------------------------------------
import re

from core import httptools
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item
from core.tmdb import infoSod

__channel__ = "videotecadiclasse"

host = "http://fetchrss.com"


def mainlist(item):
    logger.info("streamondemand.videotecadiclasse mainlist")
    itemlist = [Item(channel=__channel__,
                     title="[COLOR azure]Aggiornamenti Film[/COLOR]",
                     action="peliculas",
                     url="http://fetchrss.com/generator/generate?url=https://www.facebook.com%2FVideotecaDiClasse%2F&provider=facebook",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png")]

    return itemlist


def peliculas(item):
    logger.info("streamondemand.videotecadiclasse peliculas")
    itemlist = []

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    patron = 'This is an example of your RSS feed. Please verify that it contains all you need<br>\s*<iframe src="([^"]+)"><\/iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        scrapedthumbnail = "http://www.timeninjablog.com/wp-content/uploads/2015/12/RSS.jpg"
        scrapedtitle = "Genera RSS"
        scrapedurl = host + scrapedurl
        itemlist.append(Item(channel=__channel__,
                             action="peliculas_rss",
                             fulltitle=scrapedtitle,
                             show=scrapedtitle,
                             title=scrapedtitle,
                             url=scrapedurl,
                             thumbnail=scrapedthumbnail,
                             folder=True))
    return itemlist


def peliculas_rss(item):
    logger.info("streamondemand.videotecadiclass peliculas_rss")
    itemlist = []

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    patron = '<div class="fetch-rss-content ">\s*(.*?)<\/div>\s*<a\s*href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:
        scrapedthumbnail = ""
        scrapedplot = ""
        scrapedurl = httptools.downloadpage(scrapedurl, only_headers=True, follow_redirects=False).headers.get("location")
        txt = "streaming"
        if txt not in scrapedtitle: continue
        old = "blogspot"
        if old in scrapedtitle: continue
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.split("(")[0]
        itemlist.append(infoSod(
            Item(channel=__channel__,
                 action="findvideos",
                 contentType="movie",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True), tipo='movie'))

    return itemlist


def findvideos(item):
    logger.info("[videotecadiclasse.py] findvideos")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<a href="https://l[^=]+=([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        scrapedurl = scrapedurl.replace("&amp;", "&")
        scrapedurl = scrapedurl.replace("%2F", "/")
        scrapedurl = scrapedurl.replace("%3A", ":")
        link1 = "momentsapp"
        if link1 in scrapedurl: continue
        link2 = "instagram"
        if link2 in scrapedurl: continue
        itemlist.append(
            Item(channel=__channel__,
                 action="play",
                 title=item.title,
                 fulltitle=item.fulltitle,
                 url=scrapedurl,
                 thumbnail=item.thumbnail))
    return itemlist


def play(item):
    logger.info("[videotecadiclasse.py] play")
    data = httptools.downloadpage(item.url).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.show
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = __channel__

    return itemlist
