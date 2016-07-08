# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documaniatv.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re
import sys
import urlparse
import urllib

from core import config
from core import jsontools
from core import logger
from core import scrapertools
from core.item import Item


DEBUG = config.get_setting("debug")
host = "http://www.documaniatv.com/"
account = ( config.get_setting("documaniatvaccount") == "true" )

headers = [['User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
          ['Referer',host]]


def openconfig(item):
    if config.get_library_support():
        config.open_settings()

    if "kodi" in config.get_platform():
        import xbmc
        xbmc.executebuiltin("Container.Refresh")        
    return []


def login():
    logger.info("pelisalacarta.channels.documaniatv login")

    user = config.get_setting('documaniatvuser')
    password = config.get_setting('documaniatvpassword')
    data = scrapertools.cachePage(host, headers=headers)
    if "http://www.documaniatv.com/user/"+user in data:
        return False, user

    post = "username=%s&pass=%s&Login=Iniciar Sesión" % (user, password)
    data = scrapertools.cachePage("http://www.documaniatv.com/login.php", headers=headers, post=post)

    if "Nombre de usuario o contraseña incorrectas" in data:
        logger.info("pelisalacarta.channels.documaniatv login erróneo")
        return True, ""

    return False, user


def mainlist(item):
    logger.info("pelisalacarta.channels.documaniatv mainlist")

    itemlist = []
    itemlist.append( Item(channel=item.channel, action="novedades"  , title="Novedades"      , url="http://www.documaniatv.com/newvideos.html", thumbnail="http://i.imgur.com/qMR9sg9.png"))
    itemlist.append( Item(channel=item.channel, action="categorias" , title="Categorías y Canales" , url="http://www.documaniatv.com/browse.html", thumbnail="http://i.imgur.com/qMR9sg9.png"))
    itemlist.append( Item(channel=item.channel, action="novedades"  , title="Top"      , url="http://www.documaniatv.com/topvideos.html", thumbnail="http://i.imgur.com/qMR9sg9.png"))
    itemlist.append( Item(channel=item.channel, action="categorias" , title="Series Documentales" , url="http://www.documaniatv.com/top-series-documentales-html", thumbnail="http://i.imgur.com/qMR9sg9.png"))
    itemlist.append( Item(channel=item.channel, action="viendo"     , title="Viendo ahora" , url="http://www.documaniatv.com", thumbnail="http://i.imgur.com/qMR9sg9.png"))
    itemlist.append( Item(channel=item.channel, action="search"     , title="Buscar", thumbnail="http://i.imgur.com/qMR9sg9.png"))
    
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
    itemlist.append( Item(channel=item.channel, title=title, action=action, url=url, folder=folder))
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
        action = "play_"
        for match in bloque:
            patron = '<span class="pm-label-duration">(.*?)</span>.*?<a href="([^"]+)"' \
                     '.*?title="([^"]+)".*?data-echo="([^"]+)"'
            matches = scrapertools.find_multiple_matches(match, patron)
            for duracion, scrapedurl, scrapedtitle, scrapedthumbnail in matches:
                contentTitle = scrapedtitle
                scrapedtitle += "   ["+duracion+"]"
                scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
                if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
                itemlist.append( Item(channel=item.channel, action=action, title=scrapedtitle , url=scrapedurl,
                                thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, plot=scrapedplot, fulltitle=scrapedtitle,
                                contentTitle=contentTitle, folder=False) )
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
                itemlist.append( Item(channel=item.channel, action=action, title=scrapedtitle , url=scrapedurl,
                                thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, plot=scrapedplot, id=video_id, fulltitle=scrapedtitle,
                                contentTitle=contentTitle, folder=True) )

    # Busca enlaces de paginas siguientes...
    try:
        next_page_url = scrapertools.get_match(data,'<a href="([^"]+)">&raquo;</a>')
        next_page_url = urlparse.urljoin(host,next_page_url)
        itemlist.append( Item(channel=item.channel, action="novedades", title=">> Pagina siguiente" , url=next_page_url , thumbnail="" , plot="" , folder=True) )
    except:
        logger.info("documaniatv.novedades Siguiente pagina no encontrada")
    
    return itemlist


def categorias(item):
    logger.info("pelisalacarta.channels.documaniatv categorias")
    itemlist = []
    data = scrapertools.cachePage(item.url, headers=headers)

    patron = '<div class="pm-li-category">.*?<a href="([^"]+)"' \
             '.*?<img src="([^"]+)".*?<h3>(?:<a.*?><span.*?>|)(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedthumbnail += "|"+headers[0][0]+"="+headers[0][1]
        itemlist.append( Item(channel=item.channel, action="novedades", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, folder=True) )

    # Busca enlaces de paginas siguientes...
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)"><i class="fa fa-arrow-right">')
    if next_page_url != "":
        itemlist.append( Item(channel=item.channel, action="categorias", title=">> Pagina siguiente" , url=next_page_url , thumbnail="" , plot="" , folder=True) )
        
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
        itemlist.append( Item(channel=item.channel, action="play_", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, fulltitle=scrapedtitle, folder=False) )
    
    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.channels.documaniatv findvideos")
    itemlist = []
    
    # Se comprueba si el vídeo está ya en favoritos/ver más tarde
    url = "http://www.documaniatv.com/ajax.php?p=playlists&do=video-watch-load-my-playlists&video-id=%s" % item.id
    data = scrapertools.cachePage(url, headers=headers)
    data = jsontools.load_json(data)
    data = re.sub(r"\n|\r|\t", '', data['html'])

    itemlist.append( Item(channel=item.channel, action="play_"  , title=">> Reproducir vídeo", url=item.url, thumbnail=item.thumbnail, fulltitle=item.fulltitle, folder=False))
    if "kodi" in config.get_platform(): folder = False
    else: folder = True
    patron = '<li data-playlist-id="([^"]+)".*?onclick="playlist_(\w+)_item' \
             '.*?<span class="pm-playlists-name">(.*?)</span>.*?' \
             '<span class="pm-playlists-video-count">(.*?)</span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for playlist_id, playlist_action, playlist_title, video_count in matches:
        scrapedtitle = playlist_action.replace('remove','Eliminar de ').replace('add','Añadir a ')
        scrapedtitle += playlist_title + "   ("+video_count+")"
        itemlist.append( Item(channel=item.channel, action="acciones_playlist"  , title=scrapedtitle, id=item.id, list_id=playlist_id, url="http://www.documaniatv.com/ajax.php", folder=folder))

    if "kodi" in config.get_platform():
        itemlist.append( Item(channel=item.channel, action="acciones_playlist"  , title="Crear una nueva playlist y añadir el documental", id=item.id, url="http://www.documaniatv.com/ajax.php", folder=folder))
    itemlist.append( Item(channel=item.channel, action="acciones_playlist"  , title="Me gusta", id=item.id, url="http://www.documaniatv.com/ajax.php", folder=folder))

    return itemlist


def play_(item):
    logger.info("pelisalacarta.channels.documaniatv play_")
    itemlist = []

    import xbmc
    if  not xbmc.getCondVisibility('System.HasAddon(script.cnubis)'):
        dialog_ok("Addon no encontrado", "Para ver vídeos alojados en cnubis necesitas tener su instalado su add-on",
                  line3="Descárgalo en https://cnubis.com/kodi-pelisalacarta.html" )
        return itemlist
        
    # Descarga la pagina
    data = scrapertools.cachePage(item.url, headers=headers)
    # Busca enlace directo
    video_url = scrapertools.find_single_match(data, 'class="embedded-video"[^<]+<iframe.*?src="([^"]+)"')        

    cnubis_script = xbmc.translatePath("special://home/addons/script.cnubis/default.py")
    xbmc.executebuiltin("XBMC.RunScript(%s, url=%s&referer=%s&title=%s)" 
                        % (cnubis_script, urllib.quote_plus(video_url), urllib.quote_plus(item.url),
                        item.fulltitle))
        

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
        itemlist.append( Item(channel=item.channel, action="playlist", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, folder=True) )

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
        itemlist.append( Item(channel=item.channel, action=""  , title="Se ha añadido/eliminado correctamente", url="", folder=False))
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
        itemlist.append( Item(channel=item.channel, action="play_", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fanart=scrapedthumbnail, fulltitle=scrapedtitle, folder=False) )
    
    return itemlist    
    
    
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

def dialog_ok(heading, line1="", line2="", line3=""):
    import xbmcgui
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, line1, line2, line3)
