# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para animestream.it
# http://www.mimediacenter.info/foro/viewforum.php?f=36
#  By Costaplus
# ------------------------------------------------------------
import re
import urlparse

import xbmc

from core import config, httptools
from core import logger
from core import scrapertools
from core.item import Item

__channel__ = "animestream"

host = "http://www.animestream.it/"
hostcategoria = "http://www.animestream.it/Ricerca-Tutti-pag1"


# -----------------------------------------------------------------
def mainlist(item):
    log("mainlist", "mainlist")
    itemlist = [Item(channel=__channel__,
                     action="lista_anime",
                     title="[COLOR azure]Anime[/COLOR]",
                     url=Crea_Url(),
                     thumbnail=AnimeThumbnail,
                     fanart=AnimeFanart),
                Item(channel=__channel__,
                     action="categoria",
                     title="[COLOR azure]Categorie[/COLOR]",
                     url=hostcategoria,
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=__channel__,
                     action="search",
                     title="[COLOR orange]Cerca...[/COLOR]",
                     url="http://www.leserie.tv/index.php?do=search",
                     extra="anime",
                     thumbnail=CercaThumbnail,
                     fanart=CercaFanart)]

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def lista_anime(item):
    log("lista_anime", "lista_anime")
    itemlist = []

    patron = 'class="anime"[^<]+<.*?window.location=\'(.*?)\'.*?url\((.*?)\);">[^=]+[^<]+[^>]+[^<]+<h4>(.*?)</h4>'

    for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(item.url, patron):
        log("lista_anime",
            "scrapedurl: " + scrapedurl + " scrapedthumbnail:" + scrapedthumbnail + "scrapedtitle:" + scrapedtitle)
        scrapedthumbnail = scrapedthumbnail.replace("(", "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=__channel__,
                 action="episodios",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 fanart=urlparse.urljoin(host, scrapedthumbnail)))

    # Paginazione
    # ===========================================================
    pagina = scrapedSingle(item.url, '<div class="navc">.*?</div>', '<b.*?id="nav".*>.*?</b>[^<]+<.*?>(.*?)</a>')
    if len(pagina) > 0:
        paginaurl = Crea_Url(pagina[0], "ricerca")
        log("lista_anime.Paginazione", "Paginaurl: " + paginaurl)
        itemlist.append(
            Item(channel=__channel__,
                 action="lista_anime",
                 title=AvantiTxt,
                 url=paginaurl,
                 thumbnail=AvantiImg,
                 folder=True))
        itemlist.append(Item(channel=__channel__, action="HomePage", title=HomeTxt, folder=True))
    # ===========================================================
    return itemlist


# =================================================================

# -----------------------------------------------------------------
def lista_anime_categoria(item):
    log("lista_anime_categoria", "lista_anime_categoria")
    itemlist = []

    patron = 'class="anime"[^<]+<.*?window.location=\'(.*?)\'.*?url\((.*?)\);">[^=]+[^<]+[^>]+[^<]+<h4>(.*?)</h4>'

    for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(item.url, patron):
        log("lista_anime_categoria",
            "scrapedurl: " + scrapedurl + " scrapedthumbnail:" + scrapedthumbnail + "scrapedtitle:" + scrapedtitle)
        scrapedthumbnail = scrapedthumbnail.replace("(", "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=__channel__,
                 action="episodios",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 fanart=urlparse.urljoin(host, scrapedthumbnail)))

    # Paginazione
    # ===========================================================
    pagina = scrapedSingle(item.url, '<div class="navc">.*?</div>', '<b.*?id="nav".*>.*?</b>[^<]+<.*?>(.*?)</a>')
    if len(pagina) > 0:
        paginaurl = Crea_Url(pagina[0], "ricerca", item.title)
        log("lista_anime.Paginazione", "Paginaurl: " + paginaurl)
        itemlist.append(
            Item(channel=__channel__,
                 action="lista_anime_categoria",
                 title=AvantiTxt,
                 url=paginaurl,
                 thumbnail=AvantiImg,
                 folder=True))
        itemlist.append(Item(channel=__channel__, action="HomePage", title=HomeTxt, folder=True))
    # ===========================================================
    return itemlist


# =================================================================

# -----------------------------------------------------------------
def search(item, texto):
    log("lista_anime_categoria", "search")
    itemlist = []

    url = Crea_Url("1", "ricerca", "", texto)

    patron = 'class="anime"[^<]+<.*?window.location=\'(.*?)\'.*?url\((.*?)\);">[^=]+[^<]+[^>]+[^<]+<h4>(.*?)</h4>'

    for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(url, patron):
        log("search",
            "scrapedurl: " + scrapedurl + " scrapedthumbnail:" + scrapedthumbnail + "scrapedtitle:" + scrapedtitle)
        scrapedthumbnail = scrapedthumbnail.replace("(", "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=__channel__,
                 action="episodios",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 fanart=urlparse.urljoin(host, scrapedthumbnail)))

    return itemlist


# =================================================================
# -----------------------------------------------------------------
def categoria(item):
    log("categoria", "categoria")
    itemlist = []
    patron = '<option value="(.*?)">.*?</option>'

    for scrapedCategoria in scrapedAll(item.url, patron):
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedCategoria)
        cat = Crea_Url("", "ricerca", scrapedtitle.replace(' ', "%20"))
        if len(scrapedtitle) > 0:
            itemlist.append(
                Item(channel=__channel__,
                     action="lista_anime_categoria",
                     title=scrapedtitle,
                     url=cat,
                     thumbnail="",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     fanart=AnimeFanart))

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def episodios(item):
    itemlist = []

    patron = 'class="episodio">\s*<.*?href=([^>]+)><img.*?src=(.*?)width[^<]+<[^<]+<[^<]+<[^<]+<.*?>(.*?)</a>'
    patronvideos = '<a id="nav" href="([^"]+)">></a>'

    url = urlparse.urljoin(host, item.url)

    while True:
        for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(url, patron):

            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     contentType="episode",
                     title=scrapedtitle,
                     url=scrapedurl,
                     thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                     fulltitle=item.show + ' | ' + scrapedtitle,
                     show=item.show,
                     fanart=urlparse.urljoin(host, scrapedthumbnail)))

        data = httptools.downloadpage(urlparse.urljoin(host, item.url)).data
        matches = re.compile(patronvideos, re.DOTALL).findall(data)

        if len(matches) > 0:
            url = urlparse.urljoin(url, matches[0])
        else:
            break

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


# =================================================================

# -----------------------------------------------------------------
def findvideos(item):
    itemlist = []

    patron = '<source.*?src="(.*?)".*?>'
    for scrapedurl in scrapedAll(urlparse.urljoin(host, item.url), patron):
        url = urlparse.urljoin(host, scrapedurl)
        log("player", "url Video:" + url)
        itemlist.append(
            Item(channel=__channel__,
                 action="play",
                 title=item.title,
                 url=url,
                 thumbnail=item.thumbnail,
                 plot=item.plot,
                 fanart=item.fanart,
                 folder=False))

    return itemlist


# =================================================================

# =================================================================
# Funzioni di servizio
# -----------------------------------------------------------------
def scrapedAll(url="", patron=""):

    data = httptools.downloadpage(url).data
    MyPatron = patron
    matches = re.compile(MyPatron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    return matches


# =================================================================

# -----------------------------------------------------------------
def scrapedSingle(url="", single="", patron=""):
    data = httptools.downloadpage(url).data
    paginazione = scrapertools.find_single_match(data, single)
    matches = re.compile(patron, re.DOTALL).findall(paginazione)
    scrapertools.printMatches(matches)

    return matches


# =================================================================

# -----------------------------------------------------------------
def Crea_Url(pagina="1", azione="ricerca", categoria="", nome=""):
    # esempio
    # chiamate.php?azione=ricerca&cat=&nome=&pag=
    Stringa = host + "chiamate.php?azione=" + azione + "&cat=" + categoria + "&nome=" + nome + "&pag=" + pagina
    log("crea_Url", Stringa)
    return Stringa


# =================================================================

# -----------------------------------------------------------------
def log(funzione="", stringa="", canale=__channel__):


# =================================================================

# -----------------------------------------------------------------
def HomePage(item):
    xbmc.executebuiltin("ReplaceWindow(10024,plugin://plugin.video.streamondemand)")


# =================================================================

# =================================================================
# riferimenti di servizio
# -----------------------------------------------------------------
AnimeThumbnail = "http://img15.deviantart.net/f81c/i/2011/173/7/6/cursed_candies_anime_poster_by_careko-d3jnzg9.jpg"
AnimeFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
CategoriaThumbnail = "http://static.europosters.cz/image/750/poster/street-fighter-anime-i4817.jpg"
CategoriaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
CercaThumbnail = "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
CercaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
HomeTxt = "[COLOR yellow]Torna Home[/COLOR]"
AvantiTxt = "[COLOR orange]Successivo>>[/COLOR]"
AvantiImg = "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"