# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documaniatv.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re
import sys
import urlparse

from core import config
from core import jsontools
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import platformtools

__channel__ = "documaniatv"
__category__ = "D"
__type__ = "generic"
__title__ = "DocumaniaTV"
__language__ = "ES"

DEBUG = config.get_setting("debug")
host = "http://www.documaniatv.com/"
account = ( config.get_setting("documaniatvpassword",__channel__) != "" )

headers = [['User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
          ['Referer',host]]


def isGeneric():
    return True


def openconfig(item):
    platformtools.show_channel_settings()

    if "kodi" in config.get_platform():
        import xbmc
        xbmc.executebuiltin("Container.Refresh")
    return []


def login():
    logger.info("pelisalacarta.channels.documaniatv login")

    user = config.get_setting('documaniatvuser', __channel__)
    password = config.get_setting('documaniatvpassword', __channel__)
    data = scrapertools.cachePage(host, headers=headers)
    if "http://www.documaniatv.com/user/"+user in data:
        return False, user

    post = "username=%s&pass=%s&Login=Iniciar Sesión" % (user, password)
    data = scrapertools.cachePage("http://www.documaniatv.com/login.php", headers=headers, post=post)

    if "Nombre de usuario o contraseña incorrectas" in data:
        logger.error("login erróneo")
        return True, ""

    return False, user


def mainlist(item):
    logger.info("pelisalacarta.channels.documaniatv mainlist")

    itemlist = []
    itemlist.append( Item(channel=__channel__, action="novedades"  , title="Novedades"      , url="http://www.documaniatv.com/newvideos.html", thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/documaniatv.png"))
    itemlist.append( Item(channel=__channel__, action="categorias" , title="Categorías y Canales" , url="http://www.documaniatv.com/browse.html", thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/documaniatv.png"))
    itemlist.append( Item(channel=__channel__, action="novedades"  , title="Top"      , url="http://www.documaniatv.com/topvideos.html", thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/documaniatv.png"))
    itemlist.append( Item(channel=__channel__, action="categorias" , title="Series Documentales" , url="http://www.documaniatv.com/top-series-documentales-html", thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/documaniatv.png"))
    itemlist.append( Item(channel=__channel__, action="viendo"     , title="Viendo ahora" , url="http://www.documaniatv.com", thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/documaniatv.png"))
    itemlist.append( Item(channel=__channel__, action="search"     , title="Buscar", thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/documaniatv.png"))

    folder = False
    action = "openconfig"
    if account:
        error, user = login()
        if error:
            title = "Playlists Personales (Error en usuario y/o contraseña)"
        else:
            title = "Playlists Personales (Logueado)"
            action = "usuario"
            folder = True

    else:
        title = "Playlists Personales (Sin cuenta configurada)"
        user = ""

    url = "http://www.documaniatv.com/user/%s" % user
    itemlist.append( Item(channel=__channel__, title=title, action=action, url=url, folder=folder))

    itemlist.append(Item(channel=__channel__, action="openconfig", title="Configuración", thumbnail="http://media.tvalacarta.info/pelisalacarta/squares/thumb_configuracion.png"))

    return itemlist


def newest(categoria):
    itemlist = []
    item = Item()
    try:
        if categoria == 'documentales':
            item.url = "http://www.documaniatv.com/newvideos.html"
            itemlist= novedades(item)

            if itemlist[-1].action == "novedades":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item,texto):
    logger.info("pelisalacarta.channels.documaniatv search")
    data = scrapertools.cachePage(host, headers=headers)
    item.url = scrapertools.find_single_match(data, 'form action="([^"]+)"') + "?keywords=%s&video-id="
    texto = texto.replace(" ","+")
    item.url = item.url % texto
    try:
        return novedades(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []


def novedades(item):
    logger.info("pelisalacarta.channels.documaniatv novedades")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cachePage(item.url, headers=headers)
    # Saca el plot si lo tuviese
    scrapedplot = scrapertools.find_single_match(data, '<div class="pm-section-head">(.*?)</div>')
    if "<div" in scrapedplot:
        scrapedplot = ""
    else:
        scrapedplot = scrapertools.htmlclean(scrapedplot)
    bloque = scrapertools.find_multiple_matches(data, '<li class="col-xs-[\d] col-sm-[\d] col-md-[\d]">(.*?)</li>')

    if "Registrarse" in data:
        action = "play"
        for match in bloque:
            patron = '<span class="pm-label-duration">(.*?)</span>.*?<a href="([^"]+)"' \
                     '.*?title="([^"]+)".*?data-echo="([^"]+)"'
            matches = scrapertools.find_multiple_matches(match, patron)
            for duracion, scrapedurl, scrapedtitle, scrapedthumbnail in matches:
                contentTitle = scrapedtitle
                scrapedtitle += "   ["+duracion+"]"
                scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
                if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
                itemlist.append( Item(channel=__channel__, action=action, title=scrapedtitle , url=scrapedurl,
                                      thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, plot=scrapedplot,
                                      folder=False, contentTitle=contentTitle))
    else:
        action = "findvideos"
        for match in bloque:
            patron = '<span class="pm-label-duration">(.*?)</span>.*?onclick="watch_later_add\(([\d]+)\)' \
                     '.*?<a href="([^"]+)".*?title="([^"]+)".*?data-echo="([^"]+)"'
            matches = scrapertools.find_multiple_matches(match, patron)
            for duracion, video_id, scrapedurl, scrapedtitle, scrapedthumbnail in matches:
                contentTitle = scrapedtitle
                scrapedtitle += "   ["+duracion+"]"
                scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
                if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
                itemlist.append( Item(channel=__channel__, action=action, title=scrapedtitle , url=scrapedurl,
                                      thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, plot=scrapedplot,
                                      id=video_id, folder=True, contentTitle=contentTitle))


    # Busca enlaces de paginas siguientes...
    try:
        next_page_url = scrapertools.get_match(data,'<a href="([^"]+)">&raquo;</a>')
        next_page_url = urlparse.urljoin(host,next_page_url)
        itemlist.append( Item(channel=__channel__, action="novedades", title=">> Pagina siguiente" , url=next_page_url , thumbnail="" , plot="" , folder=True) )
    except:
        logger.error("Siguiente pagina no encontrada")

    return itemlist


def categorias(item):
    logger.info("pelisalacarta.channels.documaniatv categorias")
    itemlist = []
    data = scrapertools.cachePage(item.url,headers=headers)

    patron = '<div class="pm-li-category">.*?<a href="([^"]+)"' \
             '.*?<img src="([^"]+)".*?<h3>(?:<a.*?><span.*?>|)(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
        itemlist.append( Item(channel=__channel__, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, folder=True) )

    return itemlist


def viendo(item):
    logger.info("pelisalacarta.channels.documaniatv viendo")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cachePage(item.url, headers=headers)
    bloque = scrapertools.find_single_match(data, '<ul class="pm-ul-carousel-videos list-inline"(.*?)</ul>')
    patron = '<span class="pm-label-duration">(.*?)</span>.*?<a href="([^"]+)"' \
             '.*?title="([^"]+)".*?data-echo="([^"]+)"'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for duracion, scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle += "   ["+duracion+"]"
        scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, folder=False) )

    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.channels.documaniatv findvideos")
    itemlist = []

    # Se comprueba si el vídeo está ya en favoritos/ver más tarde
    url = "http://www.documaniatv.com/ajax.php?p=playlists&do=video-watch-load-my-playlists&video-id=%s" % item.id
    data = scrapertools.cachePage(url, headers=headers)
    data = jsontools.load_json(data)
    data = re.sub(r"\n|\r|\t", '', data['html'])

    itemlist.append( Item(channel=__channel__, action="play"  , title=">> Reproducir vídeo", url=item.url, folder=False))
    if "kodi" in config.get_platform(): folder = False
    else: folder = True
    patron = '<li data-playlist-id="([^"]+)".*?onclick="playlist_(\w+)_item' \
             '.*?<span class="pm-playlists-name">(.*?)</span>.*?' \
             '<span class="pm-playlists-video-count">(.*?)</span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for playlist_id, playlist_action, playlist_title, video_count in matches:
        scrapedtitle = playlist_action.replace('remove','Eliminar de ').replace('add','Añadir a ')
        scrapedtitle += playlist_title + "   ("+video_count+")"
        itemlist.append( Item(channel=__channel__, action="acciones_playlist"  , title=scrapedtitle, id=item.id, list_id=playlist_id, url="http://www.documaniatv.com/ajax.php", folder=folder))

    if "kodi" in config.get_platform():
        itemlist.append( Item(channel=__channel__, action="acciones_playlist"  , title="Crear una nueva playlist y añadir el documental", id=item.id, url="http://www.documaniatv.com/ajax.php", folder=folder))
    itemlist.append( Item(channel=__channel__, action="acciones_playlist"  , title="Me gusta", id=item.id, url="http://www.documaniatv.com/ajax.php", folder=folder))

    return itemlist


def play(item):
    logger.info("pelisalacarta.channels.documaniatv play")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cachePage(item.url, headers=headers)
    # Busca enlace directo
    video_url = scrapertools.find_single_match(data, '<iframe.*?src="(http://cnubis.*?)"')
    if video_url == "":
        try:
            var_url, ajax = scrapertools.find_single_match(data, '\'.preroll_timeleft.*?url:([^+]+)\+"([^"]+)"')
            url_base = scrapertools.find_single_match(data, 'var.*?' + var_url + '="([^"]+)"')
            patron = '\'.preroll_timeleft.*?data:\{"([^"]+)":"([^"]+)","' \
                     '([^"]+)":"([^"]+)","([^"]+)":"([^"]+)","([^"]+)"' \
                     ':"([^"]+)","([^"]+)":"([^"]+)","([^"]+)":"(.*?)"\}'
            match = scrapertools.find_single_match(data, patron)
            params = "{0}={1}&{2}={3}&{4}={5}&{6}={7}&{8}={9}&{10}={11}".format(match[0],match[1],match[2],
                                                                        match[3],match[4],match[5],
                                                                        match[6],match[7],match[8],
                                                                        match[9],match[10],match[11])

            url = url_base + ajax + "?" + params
            data = scrapertools.cachePage(url, headers=headers)
            video_url = scrapertools.find_single_match(data, '<iframe.*?src="(http://cnubis.*?)"')
        except:
            video_id = scrapertools.find_single_match(item.url, 'video_([0-9A-z]+)')
            url = "http://www.documaniatv.com/ajax.php?p=video&do=getplayer&vid=%s&aid=3&player=detail&playlist=" % video_id
            data = scrapertools.cachePage(url, headers=headers)
            video_url = scrapertools.find_single_match(data, '<iframe.*?src="(http://cnubis.*?)"')

    # Busca los enlaces a los videos
    video_itemlist = servertools.find_video_items(data=video_url)
    for video_item in video_itemlist:
        itemlist.append( Item(channel=__channel__ , action="play" , server=video_item.server, title=item.title+video_item.title,url=video_item.url, thumbnail=video_item.thumbnail, plot=video_item.plot, folder=False))

    return itemlist


def usuario(item):
    logger.info("pelisalacarta.channels.documaniatv usuario")
    itemlist = []
    data = scrapertools.cachePage(item.url, headers=headers)
    profile_id = scrapertools.find_single_match(data, 'data-profile-id="([^"]+)"')
    url = "http://www.documaniatv.com/ajax.php?p=profile&do=profile-load-playlists&uid=%s" % profile_id

    data = scrapertools.cachePage(url, headers=headers)
    data = jsontools.load_json(data)
    data = data['html']

    patron = '<div class="pm-video-thumb">.*?src="([^"]+)".*?' \
             '<span class="pm-pl-items">(.*?)</span>(.*?)</div>' \
             '.*?<h3.*?href="([^"]+)".*?title="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, items, videos, scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace("Historia",'Historial')
        scrapedtitle += " ("+items+videos+")"
        if "no-thumbnail" in scrapedthumbnail:
            scrapedthumbnail = ""
        else:
            scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
        itemlist.append( Item(channel=__channel__, action="playlist", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, folder=True) )

    return itemlist


def acciones_playlist(item):
    logger.info("pelisalacarta.channels.documaniatv acciones_playlist")
    itemlist = []
    if item.title == "Crear una nueva playlist y añadir el documental":
        texto = dialog_input(heading="Introduce el título de la nueva playlist")
        if texto != "":
            post= "p=playlists&do=create-playlist&title=%s&visibility=1&video-id=%s&ui=video-watch" % (texto, item.id)
            data = scrapertools.cachePage(item.url, headers=headers, post=post)

    elif item.title != "Me gusta":
        if "Eliminar" in item.title: action = "remove-from-playlist"
        else: action = "add-to-playlist"
        post = "p=playlists&do=%s&playlist-id=%s&video-id=%s" % (action, item.list_id, item.id)
        data = scrapertools.cachePage(item.url, headers=headers, post=post)
    else:
        item.url = "http://www.documaniatv.com/ajax.php?vid=%s&p=video&do=like" % item.id
        data = scrapertools.cachePage(item.url, headers=headers)

    try:
        dialog_notification(item.title, "Se ha añadido/eliminado correctamente")
        import xbmc
        xbmc.executebuiltin("Container.Refresh")
    except:
        itemlist.append( Item(channel=__channel__, action=""  , title="Se ha añadido/eliminado correctamente", url="", folder=False))
        return itemlist


def playlist(item):
    logger.info("pelisalacarta.channels.documaniatv playlist")
    itemlist = []
    data = scrapertools.cachePage(item.url, headers=headers)
    patron = '<div class="pm-pl-list-index.*?src="([^"]+)".*?' \
             '<a href="([^"]+)".*?>(.*?)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedurl, scrapedtitle  in matches:
        scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, folder=False) )

    return itemlist


# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    items = novedades(mainlist_items[0])
    bien = False
    for singleitem in items:
        mirrors = servertools.find_video_items( item=singleitem )
        if len(mirrors)>0:
            bien = True
            break

    return bien


def dialog_notification(heading, message, icon=0, time=5000, sound=True):
    import xbmcgui
    dialog = xbmcgui.Dialog()
    l_icono=(xbmcgui.NOTIFICATION_INFO , xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR)
    dialog.notification (heading, message, l_icono[icon], time, sound)


def dialog_input(default="", heading="", hidden=False):
    import xbmc
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return ""