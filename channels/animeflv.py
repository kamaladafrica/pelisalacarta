# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re
import urlparse

from channels import renumbertools
from core import httptools
from core import jsontools
from core import logger
from core import scrapertools
from core.item import Item

HOST = "http://animeflv.net/"


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Últimos episodios", url=HOST))
    itemlist.append(Item(channel=item.channel, action="novedades_anime", title="Últimos animes", url=HOST))
    itemlist.append(Item(channel=item.channel, action="listado", title="Animes", url=HOST + "browse?order=title"))

    itemlist.append(Item(channel=item.channel, title="Buscar por:"))
    itemlist.append(Item(channel=item.channel, action="search", title="    Título", url=HOST + "browse"))
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Género", url=HOST + "browse",
                         extra="genre"))
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Tipo", url=HOST + "browse",
                         extra="type"))
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Año", url=HOST + "browse",
                         extra="year"))
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Estado", url=HOST + "browse",
                         extra="status"))

    if renumbertools.context:
        itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    item.url = urlparse.urljoin(HOST, "api/animes/search")
    texto = texto.replace(" ", "+")
    post = "value=%s" % texto
    data = httptools.downloadpage(item.url, post=post).data

    dict_data = jsontools.load_json(data)

    for e in dict_data:
        if e["id"] != e["last_id"]:
            _id = e["last_id"]
        else:
            _id = e["id"]

        url = "%sanime/%s/%s" % (HOST, _id, e["slug"])
        title = e["title"]
        thumbnail = "%suploads/animes/covers/%s.jpg" % (HOST, e["id"])
        new_item = item.clone(action="episodios", title=title, url=url, thumbnail=thumbnail)

        if e["type"] != "movie":
            new_item.show = title
            new_item.context = renumbertools.context
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title

        itemlist.append(new_item)

    return itemlist


def search_section(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    patron = 'id="%s_select"[^>]+>(.*?)</select>' % item.extra
    data = scrapertools.find_single_match(data, patron)

    matches = re.compile('<option value="([^"]+)">(.*?)</option>', re.DOTALL).findall(data)

    for _id, title in matches:
        url = "%s?%s=%s&order=title" % (item.url, item.extra, _id)
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url,
                             context=renumbertools.context))

    return itemlist


def newest(categoria):
    itemlist = []

    if categoria == 'anime':
        itemlist = novedades_episodios(Item(url="http://animeflv.net/"))

    return itemlist


def novedades_episodios(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, '<ul class="ListEpisodios[^>]+>(.*?)</ul>')

    matches = re.compile('<a href="([^"]+)"[^>]+>.+?<img src="([^"]+)".+?"Capi">(.*?)</span>'
                         '<strong class="Title">(.*?)</strong>', re.DOTALL).findall(data)
    itemlist = []

    for url, thumbnail, str_episode, show in matches:

        try:
            episode = int(str_episode.replace("Ep. ", ""))
        except ValueError:
            season = 1
            episode = 1
        else:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.show, 1, episode)

        title = "%s: %sx%s" % (show, season, str(episode).zfill(2))
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)

        new_item = Item(channel=item.channel, action="findvideos", title=title, url=url, show=show, thumbnail=thumbnail,
                        fulltitle=title)

        itemlist.append(new_item)

    return itemlist


def novedades_anime(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, '<ul class="ListAnimes[^>]+>(.*?)</ul>')

    matches = re.compile('<img src="([^"]+)".+?<span class=.+?>(.*?)</span>.+?<a href="([^"]+)">(.*?)</a>',
                         re.DOTALL).findall(data)
    itemlist = []

    for thumbnail, _type, url, title in matches:

        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)

        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        fulltitle=title)
        if _type != "Película":
            new_item.show = title
            new_item.context = renumbertools.context
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title

        itemlist.append(new_item)

    return itemlist


def listado(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    url_pagination = scrapertools.find_single_match(data, '<li class="active">.*?</li><li><a href="([^"]+)">')

    data = scrapertools.find_multiple_matches(data, '<ul class="ListAnimes[^>]+>(.*?)</ul>')
    data = "".join(data)

    matches = re.compile('<img src="([^"]+)".+?<span class=.+?>(.*?)</span>.+?<a href="([^"]+)">(.*?)</a>.+?'
                         'class="Desc ScrlV"><p>(.*?)</p>', re.DOTALL).findall(data)

    itemlist = []

    for thumbnail, _type, url, title, plot in matches:

        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)

        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        fulltitle=title, plot=plot)

        if _type == "Anime":
            new_item.show = title
            new_item.context = renumbertools.context
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title

        itemlist.append(new_item)

    if url_pagination:
        url = urlparse.urljoin(HOST, url_pagination)
        title = ">> Pagina Siguiente"

        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)

    if item.plot == "":
        item.plot = scrapertools.find_single_match(data, 'Description[^>]+><p>(.*?)</p>')

    data = scrapertools.find_single_match(data, '<div class="Sect Episodes">(.*?)</div>')
    matches = re.compile('<a href="([^"]+)"[^>]+>(.+?)<', re.DOTALL).findall(data)

    for url, title in matches:
        title = title.strip()
        url = urlparse.urljoin(item.url, url)
        thumbnail = item.thumbnail

        try:
            episode = int(scrapertools.find_single_match(title, "^.+?\s(\d+)$"))
        except ValueError:
            season = 1
            episode = 1
        else:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.show, 1, episode)

        title = "%s: %sx%s" % (item.title, season, str(episode).zfill(2))

        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail, fulltitle=title,
                                   fanart=thumbnail))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    list_videos = scrapertools.find_multiple_matches(data, 'video\[\d\]\s=\s\'<iframe.+?src="([^"]+)"')

    logger.info("data=%s " % list_videos)

    aux_url = []
    for e in list_videos:
        if e.startswith("https://s3.animeflv.com/embed.php?server="):
            pass
            # server = scrapertools.find_single_match(e, 'server=(.*?)&')
            # e = e.replace("embed", "check")
            # data = httptools.downloadpage(e).data
            # logger.info("datito %s" % data)
            # if '{"error": "Por favor intenta de nuevo en unos segundos", "sleep": 3}' in data:
            #     import time
            #     time.sleep(5)
            #     data = httptools.downloadpage(e).data
            #     logger.info("datito %s" % data)
            #
            # url = scrapertools.find_single_match(data, '"file":"([^"]+)"')
            # url = url.replace("\/", "/")
            #
            # itemlist.append(item.clone(title="Enlace encontrado en %s" % server, url=url))
            #
        else:
            aux_url.append(e)

    from core import servertools
    itemlist.extend(servertools.find_video_items(data=",".join(aux_url)))
    for videoitem in itemlist:
        videoitem.fulltitle = item.fulltitle
        videoitem.channel = item.channel
        videoitem.thumbnail = item.thumbnail

    return itemlist
