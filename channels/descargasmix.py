# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para Descargasmix
# Por SeiTaN, robalo y Cmos
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urllib

from core import config
from core import httptools
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item

__modo_grafico__ = config.get_setting("modo_grafico", "descargasmix")
__perfil__ = int(config.get_setting("perfil", "descargasmix"))

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]
color1, color2, color3 = perfil[__perfil__]


def mainlist(item):
    logger.info()
    itemlist = []
    item.text_color = color1

    kodi17 = False
    if config.is_xbmc():
        import xbmc
        xbmc_version = int(xbmc.getInfoLabel("System.BuildVersion").split(".", 1)[0])
        if xbmc_version > 16:
            kodi17 = True

    if not kodi17:
        title = "Este canal solo es compatible con Kodi y en su versión 17 (Krypton) o superior"
        itemlist.append(item.clone(title=title, action=""))
        return itemlist

    itemlist.append(item.clone(title="Películas", action="lista", fanart="http://i.imgur.com/c3HS8kj.png"))
    itemlist.append(item.clone(title="Series", action="lista_series", fanart="http://i.imgur.com/9loVksV.png"))
    itemlist.append(item.clone(title="Documentales", action="entradas", url="https://desmix.net/documentales/",
                               fanart="http://i.imgur.com/Q7fsFI6.png"))
    itemlist.append(item.clone(title="Anime", action="entradas", url="https://desmix.net/anime/",
                               fanart="http://i.imgur.com/whhzo8f.png"))
    itemlist.append(item.clone(title="Deportes", action="entradas", url="https://desmix.net/deportes/",
                               fanart="http://i.imgur.com/ggFFR8o.png"))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(title="Buscar...", action="search"))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))

    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    try:
        item.url = "https://desmix.net/?s=" + texto
        return busqueda(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def busqueda(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    contenido = ['Películas', 'Series', 'Documentales', 'Anime', 'Deportes', 'Miniseries', 'Vídeos']
    bloque = scrapertools.find_single_match(data, '<div id="content" role="main">(.*?)<div id="sidebar" '
                                                  'role="complementary">')
    patron = '<a class="clip-link".*?href="([^"]+)".*?<img alt="([^"]+)" src="([^"]+)"' \
             '.*?<span class="overlay.*?>(.*?)<.*?<p class="stats">(.*?)</p>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, info, scrapedcat in matches:
        if not [True for c in contenido if c in scrapedcat]:
            continue
        if not scrapedthumbnail.startswith("http"):
            scrapedthumbnail = "https:" + scrapedthumbnail
        scrapedthumbnail = scrapedthumbnail.replace("-129x180", "")
        if ("Películas" in scrapedcat or "Documentales" in scrapedcat) and "Series" not in scrapedcat:
            titulo = scrapedtitle.split("[")[0]
            if info:
                scrapedtitle += " [%s]" % unicode(info, "utf-8").capitalize().encode("utf-8")
            itemlist.append(item.clone(action="findvideos", title=scrapedtitle, url=scrapedurl, contentTitle=titulo,
                                       thumbnail=scrapedthumbnail, fulltitle=titulo, contentType="movie"))
        else:
            itemlist.append(item.clone(action="episodios", title=scrapedtitle, url=scrapedurl,
                                       thumbnail=scrapedthumbnail, fulltitle=scrapedtitle, contentTitle=scrapedtitle,
                                       show=scrapedtitle, contentType="tvshow"))

    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink".*?href="([^"]+)"')
    if next_page != "":
        itemlist.append(item.clone(action="busqueda", title=">> Siguiente", url=next_page))

    return itemlist


def lista(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Novedades", action="entradas", url="https://desmix.net/peliculas"))
    itemlist.append(item.clone(title="Estrenos", action="entradas", url="https://desmix.net/peliculas/estrenos"))
    itemlist.append(item.clone(title="Dvdrip", action="entradas", url="https://desmix.net/peliculas/dvdrip"))
    itemlist.append(item.clone(title="HD (720p/1080p)", action="entradas", url="https://desmix.net/peliculas/hd"))
    itemlist.append(item.clone(title="HDRIP", action="entradas", url="https://desmix.net/peliculas/hdrip"))
    itemlist.append(item.clone(title="Latino", action="entradas",
                               url="https://desmix.net/peliculas/latino-peliculas"))
    itemlist.append(item.clone(title="VOSE", action="entradas", url="https://desmix.net/peliculas/subtituladas"))
    itemlist.append(item.clone(title="3D", action="entradas", url="https://desmix.net/peliculas/3d"))

    return itemlist


def lista_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Novedades", action="entradas", url="https://desmix.net/series/"))
    itemlist.append(item.clone(title="Miniseries", action="entradas", url="https://desmix.net/series/miniseries"))

    return itemlist


def entradas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    data = httptools.downloadpage(item.url).data

    bloque = scrapertools.find_single_match(data, '<div id="content" role="main">(.*?)<div id="sidebar" '
                                                  'role="complementary">')
    contenido = ["series", "deportes", "anime", 'miniseries']
    c_match = [True for match in contenido if match in item.url]
    # Patron dependiendo del contenido
    if True in c_match:
        patron = '<a class="clip-link".*?href="([^"]+)".*?<img alt="([^"]+)" src="([^"]+)"' \
                 '.*?<span class="overlay(|[^"]+)">'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedinfo in matches:
            if scrapedinfo != "":
                scrapedinfo = scrapedinfo.replace(" ", "").replace("-", " ")

                scrapedinfo = "  [%s]" % unicode(scrapedinfo, "utf-8").capitalize().encode("utf-8")
            titulo = scrapedtitle + scrapedinfo
            titulo = scrapertools.decodeHtmlentities(titulo)
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
            if not scrapedthumbnail.startswith("http"):
                scrapedthumbnail = "https:" + scrapedthumbnail
            scrapedthumbnail = scrapedthumbnail.replace("-129x180", "")
            scrapedthumbnail = scrapedthumbnail.rsplit("/", 1)[0] + "/" + \
                               urllib.quote(scrapedthumbnail.rsplit("/", 1)[1])
            if "series" in item.url or "anime" in item.url:
                item.show = scrapedtitle
            itemlist.append(item.clone(action="episodios", title=titulo, url=scrapedurl, thumbnail=scrapedthumbnail,
                                       fulltitle=scrapedtitle, contentTitle=scrapedtitle, contentType="tvshow"))
    else:
        patron = '<a class="clip-link".*?href="([^"]+)".*?<img alt="([^"]+)" src="([^"]+)"' \
                 '.*?<span class="overlay.*?>(.*?)<.*?<p class="stats">(.*?)</p>'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedurl, scrapedtitle, scrapedthumbnail, info, categoria in matches:
            titulo = scrapertools.decodeHtmlentities(scrapedtitle)
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.split("[")[0])
            action = "findvideos"
            show = ""
            if "Series" in categoria:
                action = "episodios"
                show = scrapedtitle
            elif categoria and categoria != "Películas" and categoria != "Documentales":
                try:
                    titulo += " [%s]" % categoria.rsplit(", ", 1)[1]
                except:
                    titulo += " [%s]" % categoria
                if 'l-espmini' in info:
                    titulo += " [ESP]"
                if 'l-latmini' in info:
                    titulo += " [LAT]"
                if 'l-vosemini' in info:
                    titulo += " [VOSE]"

            if info:
                titulo += " [%s]" % unicode(info, "utf-8").capitalize().encode("utf-8")

            if not scrapedthumbnail.startswith("http"):
                scrapedthumbnail = "https:" + scrapedthumbnail
            scrapedthumbnail = scrapedthumbnail.replace("-129x180", "")
            scrapedthumbnail = scrapedthumbnail.rsplit("/", 1)[0] + "/" + \
                               urllib.quote(scrapedthumbnail.rsplit("/", 1)[1])
            itemlist.append(item.clone(action=action, title=titulo, url=scrapedurl, thumbnail=scrapedthumbnail,
                                       fulltitle=scrapedtitle, contentTitle=scrapedtitle, viewmode="movie_with_plot",
                                       show=show, contentType="movie"))

    # Paginación
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink".*?href="([^"]+)"')
    if next_page:
        itemlist.append(item.clone(title=">> Siguiente", url=next_page, text_color=color3))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    patron = '(<ul class="menu" id="seasons-list">.*?<div class="section-box related-posts">)'
    bloque = scrapertools.find_single_match(data, patron)
    matches = scrapertools.find_multiple_matches(bloque, '<div class="polo".*?>(.*?)</div>')
    for scrapedtitle in matches:
        scrapedtitle = scrapedtitle.strip()
        new_item = item.clone()
        new_item.infoLabels['season'] = scrapedtitle.split(" ", 1)[0].split("x")[0]
        new_item.infoLabels['episode'] = scrapedtitle.split(" ", 1)[0].split("x")[1]
        if item.fulltitle != "Añadir esta serie a la biblioteca":
            title = item.fulltitle + " " + scrapedtitle.strip()
        else:
            title = scrapedtitle.strip()
        itemlist.append(new_item.clone(action="findvideos", title=title, extra=scrapedtitle, fulltitle=title,
                                       contentType="episode"))

    itemlist.sort(key=lambda it: it.title, reverse=True)
    item.plot = scrapertools.find_single_match(data, '<strong>SINOPSIS</strong>:(.*?)</p>')
    if item.show != "" and item.extra == "":
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        if config.get_library_support():
            itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la biblioteca", url=item.url,
                                 action="add_serie_to_library", extra="episodios", show=item.show,
                                 text_color="green"))

        try:
            from core import tmdb
            tmdb.set_infoLabels_itemlist(itemlist[:-2], __modo_grafico__)
        except:
            pass

    return itemlist


def epienlaces(item):
    logger.info()
    itemlist = []
    item.text_color = color3

    data = httptools.downloadpage(item.url).data
    data = data.replace("\n", "").replace("\t", "")

    # Bloque de enlaces
    patron = '<div class="polo".*?>%s(.*?)(?:<div class="polo"|</li>)' % item.extra.strip()
    bloque = scrapertools.find_single_match(data, patron)

    patron = '<div class="episode-server">.*?data-sourcelk="([^"]+)"' \
             '.*?data-server="([^"]+)"' \
             '.*?<div class="caliycola">(.*?)</div>'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    itemlist.append(item.clone(action="", title="Enlaces Online/Descarga", text_color=color1))
    lista_enlaces = []
    for scrapedurl, scrapedserver, scrapedcalidad in matches:
        if scrapedserver == "ul":
            scrapedserver = "uploadedto"
        if scrapedserver == "streamin":
            scrapedserver = "streaminto"
        titulo = "    %s [%s]" % (unicode(scrapedserver, "utf-8").capitalize().encode("utf-8"), scrapedcalidad)
        # Enlaces descarga
        if scrapedserver == "magnet":
            itemlist.insert(0, item.clone(action="play", title=titulo, server="torrent", url=scrapedurl))
        else:
            mostrar_server = True
            if config.get_setting("hidepremium") == "true":
                mostrar_server = servertools.is_server_enabled(scrapedserver)
            if mostrar_server:
                try:
                    lista_enlaces.append(item.clone(action="play", title=titulo, server=scrapedserver, url=scrapedurl,
                                                    extra=item.url))
                except:
                    pass
    lista_enlaces.reverse()
    itemlist.extend(lista_enlaces)

    if itemlist[0].server == "torrent":
        itemlist.insert(0, item.clone(action="", title="Enlaces Torrent", text_color=color1))

    return itemlist


def findvideos(item):
    logger.info()
    if item.extra and item.extra != "findvideos":
        return epienlaces(item)
    itemlist = []
    item.text_color = color3

    data = httptools.downloadpage(item.url).data

    item.plot = scrapertools.find_single_match(data, 'SINOPSIS(?:</span>|</strong>):(.*?)</p>')
    year = scrapertools.find_single_match(data, '(?:<span class="bold">|<strong>)AÑO(?:</span>|</strong>):\s*(\d+)')
    if year:
        try:
            from core import tmdb
            item.infoLabels['year'] = year
            tmdb.set_infoLabels_item(item, __modo_grafico__)
        except:
            pass

    old_format = False
    # Patron torrent antiguo formato
    if "Enlaces de descarga</div>" in data:
        old_format = True
        matches = scrapertools.find_multiple_matches(data, 'class="separate3 magnet".*?href="([^"]+)"')
        for scrapedurl in matches:
            title = "[Torrent] "
            title += urllib.unquote(scrapertools.find_single_match(scrapedurl, 'dn=(.*?)(?i)WWW.DescargasMix'))
            itemlist.append(item.clone(action="play", server="torrent", title=title, url=scrapedurl,
                                       text_color="green"))

    # Patron online
    data_online = scrapertools.find_single_match(data, 'Ver online</div>(.*?)<div class="section-box related-posts">')
    if data_online:
        title = "Enlaces Online"
        if '"l-latino2"' in data_online:
            title += " [LAT]"
        elif '"l-esp2"' in data_online:
            title += " [ESP]"
        elif '"l-vose2"' in data_online:
            title += " [VOSE]"

        patron = 'make_links.*?,[\'"]([^"\']+)["\']'
        matches = scrapertools.find_multiple_matches(data_online, patron)
        for i, code in enumerate(matches):
            enlace = mostrar_enlaces(code)
            enlaces = servertools.findvideos(data=enlace[0])
            if enlaces and "peliculas.nu" not in enlaces:
                if i == 0:
                    extra_info = scrapertools.find_single_match(data_online, '<span class="tooltiptext">(.*?)</span>')
                    size = scrapertools.find_single_match(data_online, '(?i)TAMAÑO:\s*(.*?)<').strip()

                    if size:
                        title += " [%s]" % size
                    new_item = item.clone(title=title, action="", text_color=color1)
                    if extra_info:
                        extra_info = scrapertools.htmlclean(extra_info)
                        new_item.infoLabels["plot"] = extra_info
                        new_item.title += " +INFO"
                    itemlist.append(new_item)

                title = "   Ver vídeo en " + enlaces[0][2]
                itemlist.append(item.clone(action="play", server=enlaces[0][2], title=title, url=enlaces[0][1]))
    scriptg = scrapertools.find_single_match(data, "<script type='text/javascript'>str='([^']+)'")
    if scriptg:
        gvideo = urllib.unquote_plus(scriptg.replace("@", "%"))
        url = scrapertools.find_single_match(gvideo, 'src="([^"]+)"')
        if url:
            itemlist.append(item.clone(action="play", server="directo", url=url, extra=item.url,
                                       title="   Ver vídeo en Googlevideo (Máxima calidad)"))

    # Patron descarga
    patron = '<div class="(?:floatLeft |)double(?:nuevo|)">(.*?)</div>(.*?)' \
             '(?:<div(?: id="mirrors"|) class="(?:contentModuleSmall |)mirrors">|<div class="section-box related-' \
             'posts">)'
    bloques_descarga = scrapertools.find_multiple_matches(data, patron)
    for title_bloque, bloque in bloques_descarga:
        if title_bloque == "Ver online":
            continue
        if '"l-latino2"' in bloque:
            title_bloque += " [LAT]"
        elif '"l-esp2"' in bloque:
            title_bloque += " [ESP]"
        elif '"l-vose2"' in bloque:
            title_bloque += " [VOSE]"

        extra_info = scrapertools.find_single_match(bloque, '<span class="tooltiptext">(.*?)</span>')
        size = scrapertools.find_single_match(bloque, '(?i)TAMAÑO:\s*(.*?)<').strip()

        if size:
            title_bloque += " [%s]" % size
        new_item = item.clone(title=title_bloque, action="", text_color=color1)
        if extra_info:
            extra_info = scrapertools.htmlclean(extra_info)
            new_item.infoLabels["plot"] = extra_info
            new_item.title += " +INFO"
        itemlist.append(new_item)

        if '<div class="subiendo">' in bloque:
            itemlist.append(item.clone(title="   Los enlaces se están subiendo", action=""))
            continue
        patron = 'class="separate.*? ([^"]+)".*?(?:make_links.*?,|href=)[\'"]([^"\']+)["\']'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for scrapedserver, scrapedurl in matches:
            if (scrapedserver == "ul") | (scrapedserver == "uploaded"):
                scrapedserver = "uploadedto"
            titulo = unicode(scrapedserver, "utf-8").capitalize().encode("utf-8")
            if titulo == "Magnet" and old_format:
                continue
            elif titulo == "Magnet" and not old_format:
                title = "   Enlace Torrent"
                itemlist.append(item.clone(action="play", server="torrent", title=title, url=scrapedurl,
                                           text_color="green"))
                continue
            mostrar_server = True
            if config.get_setting("hidepremium") == "true":
                mostrar_server = servertools.is_server_enabled(scrapedserver)
            if mostrar_server:
                try:
                    servers_module = __import__("servers." + scrapedserver)
                    # Saca numero de enlaces
                    urls = mostrar_enlaces(scrapedurl)
                    numero = str(len(urls))
                    titulo = "   %s - Nº enlaces: %s" % (titulo, numero)
                    itemlist.append(item.clone(action="enlaces", title=titulo, extra=scrapedurl))
                except:
                    pass

    itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                               text_color="magenta"))
    if item.extra != "findvideos" and config.get_library_support():
        itemlist.append(Item(channel=item.channel, title="Añadir a la biblioteca", action="add_pelicula_to_library",
                             extra="findvideos", url=item.url, infoLabels={'title': item.fulltitle},
                             fulltitle=item.fulltitle, text_color="green"))

    return itemlist


def play(item):
    logger.info()
    itemlist = []
    if "enlacesmix.com" in item.url:
        if not item.url.startswith("http:"):
            item.url = "https:" + item.url
        data = httptools.downloadpage(item.url, add_referer=True).data
        item.url = scrapertools.find_single_match(data, 'iframe src="([^"]+)"')

        enlaces = servertools.findvideos(data=item.url)
        if enlaces:
            itemlist.append(item.clone(action="play", server=enlaces[0][2], url=enlaces[0][1]))
    elif item.server == "directo":
        data = httptools.downloadpage(item.url, add_referer=True).data
        subtitulo = scrapertools.find_single_match(data, "var subtitulo='([^']+)'")
        calidades = ["1080p", "720p", "480p", "360p"]
        for i in range(0, len(calidades)):
            url_redirect = scrapertools.find_single_match(data, "{file:'([^']+)',label:'" + calidades[i] + "'")
            if url_redirect:
                url_video = httptools.downloadpage(url_redirect, follow_redirects=False, add_referer=True,
                                                   only_headers=True).headers["location"]
                if url_video:
                    url_video = url_video.replace(",", "%2C")
                    itemlist.append(item.clone(url=url_video, subtitle=subtitulo))
                    break
    elif not item.url.startswith("http"):
        post = "source=%s&action=obtenerurl" % urllib.quote(item.url)
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        data = httptools.downloadpage("https://desmix.net/wp-admin/admin-ajax.php", post=post, headers=headers).data

        url = scrapertools.find_single_match(data, 'url":"([^"]+)"').replace("\\", "")
        enlaces = servertools.findvideos(data=url)
        if enlaces:
            itemlist.append(item.clone(action="play", server=enlaces[0][2], url=enlaces[0][1]))
    else:
        itemlist.append(item.clone())

    return itemlist


def enlaces(item):
    logger.info()
    itemlist = []

    urls = mostrar_enlaces(item.extra)
    numero = len(urls)
    for enlace in urls:
        enlaces = servertools.findvideos(data=enlace)
        if enlaces:
            for link in enlaces:
                if "/folder/" in enlace:
                    titulo = link[0]
                else:
                    titulo = "%s - Enlace %s" % (item.title.split("-")[0], str(numero))
                    numero -= 1
                itemlist.append(item.clone(action="play", server=link[2], title=titulo, url=link[1]))

    itemlist.sort(key=lambda it: it.title)
    return itemlist


def mostrar_enlaces(data):
    import base64
    data = data.split(",")
    len_data = len(data)
    urls = []
    for i in range(0, len_data):
        url = []
        value1 = base64.b64decode(data[i])
        value2 = value1.split("-")
        for j in range(0, len(value2)):
            url.append(chr(int(value2[j])))

        urls.append("".join(url))

    return urls
