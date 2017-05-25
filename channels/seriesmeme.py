# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import re
import urlparse

from channels import filtertools
from core import config
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools

host = "https://seriesmeme.com/"

def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="lista_gen", title="Novedades", url=host))
    itemlist.append(Item(channel=item.channel, action="lista", title="Series", url=urlparse.urljoin(host, "/lista")))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Categorias", url=host))
    itemlist.append(Item(channel=item.channel, action="alfabetico", title="Listado Alfabetico", url=host))
    itemlist.append(Item(channel=item.channel, action="top", title="Top Series", url=host))
    #itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=urlparse.urljoin(host, "?s=")))	
    return itemlist
"""
def search(item, texto):
    logger.info()
    texto = texto.replace(" ","+")
    item.url = item.url+texto
    if texto!='':
       return lista(item)
"""
def categorias(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_cat='<li id="menu-item-15068" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    categorias=scrapertools.find_single_match(data,patron_cat)
    patron = '<li id="menu-item-.+?" class=".+?"><a href="([^"]+)">([^"]+)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(categorias, patron)
    for link, name in matches:
        title=name
        url=link
        itemlist.append(item.clone(title=title, url=url, plot=title, action="lista_gen", show=title))
    return itemlist

def alfabetico(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_alf1='<li id="menu-item-15069" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    patron_alf2='<li id="menu-item-15099" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    alfabeto1=scrapertools.find_single_match(data,patron_alf1)
    alfabeto2=scrapertools.find_single_match(data,patron_alf2)
    alfabeto=alfabeto1+alfabeto2
    patron = '<li id="menu-item-.+?" class=".+?"><a href="([^"]+)">([^"]+)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(alfabeto, patron)
    for link, name in matches:
        title=name
        url=link
        itemlist.append(item.clone(title=title, url=url, plot=title, action="lista_gen", show=title))
    return itemlist

def top(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_top='<li id="menu-item-15087" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    top=scrapertools.find_single_match(data,patron_top)
    patron = '<a href="([^"]+)">([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(top, patron)
    for link, name in matches:
        title=name
        url=link
        itemlist.append(item.clone(title=title, url=url, plot=title, action="lista_gen", show=title))
    return itemlist

def lista_gen(item):
    logger.info()

    itemlist = []

    data1 = httptools.downloadpage(item.url).data
    data1 = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data1)
    patron_sec ='<section class="content">.+?<\/section>'
    data = scrapertools.find_single_match(data1, patron_sec)
    patron = '<article id=.+? class=.+?><div.+?>'
    patron += '<a href="([^"]+)" title="([^"]+)'# scrapedurl, # scrapedtitle
    patron += ' Capítulos Completos ([^"]+)">' # scrapedlang
    patron += '<img.+? data-src=.+? data-lazy-src="([^"]+)"' # scrapedthumbnail
    matches = scrapertools.find_multiple_matches(data, patron)
    i=0
    for scrapedurl, scrapedtitle, scrapedlang, scrapedthumbnail in matches:
        i=i+1
        if 'HD' in scrapedlang:
            scrapedlang = scrapedlang.replace('HD','')
        title=scrapedtitle+" [ "+scrapedlang+"]"
        itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail, action="episodios", show=scrapedtitle))

    #Paginacion
    patron_pag='<a class="nextpostslink" .+ href="([^"]+)">'
    next_page_url = scrapertools.find_single_match(data,patron_pag)

    if next_page_url!="" and i!=1:
        item.url=next_page_url
        import inspect
        itemlist.append(Item(channel = item.channel,action = "lista_gen",title = ">> Página siguiente", url = next_page_url, thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'))

    return itemlist


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li><strong><a href="([^"]+)">([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for link, name in matches:
        title=name
        url=link
        itemlist.append(item.clone(title=title, url=url, plot=title, action="episodios", show=title))
    return itemlist

def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    logger.info("episa"+data)
    patron_caps = '<li><strong><a href="([^"]+)">([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data, patron_caps)

    show = scrapertools.find_single_match(data,'<pre><strong>.+?: (.+?)<\/strong>')

    for link, cap in matches:
        title = cap
        url=link
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, show=show))

    if config.get_library_support() and len(itemlist) > 0:

        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la biblioteca de Kodi", url=item.url,

                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist