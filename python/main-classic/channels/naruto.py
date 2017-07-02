# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para Naruto
# http://www.mimediacenter.info/foro/viewforum.php?f=36
#  By Zanzibar82
# ------------------------------------------------------------

import re

from core import httptools
from core import scrapertools
from core.item import Item

__channel__ = "naruto"

host = "http://manganimenod.it/"
home = "http://manganimenod.it/episodi.php?a=NARUTO1"


# -----------------------------------------------------------------
def mainlist(item):
    itemlist = []

    patron = '<div class="ep"><a href="(.*?)"><.*?title="(.*?)">'

    for scrapedurl, scrapedtitle in scrapedAll(home, patron):
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=__channel__,
                 action="findvideos",
                 title=scrapedtitle,
                 url=host + scrapedurl,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 thumbnail="http://i46.tinypic.com/14njw2f.png",
                 fanart="http://www.animenewsnetwork.com/thumbnails/crop900x350/video/category/62/key_art_naruto.jpg"))

    return itemlist


# =================================================================
# Funzioni di servizio
# =================================================================

# -----------------------------------------------------------------

def scrapedAll(url="", patron=""):
    data = httptools.downloadpage(url).data
    MyPatron = patron
    matches = re.compile(MyPatron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    return matches

# =================================================================
