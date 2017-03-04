# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canal (cinecalidad) por Hernan_Ar_c
# ------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb

host=''
thumbmx='http://flags.fmcdn.net/data/flags/normal/mx.png'
thumbes='http://flags.fmcdn.net/data/flags/normal/es.png'
thumbbr='http://flags.fmcdn.net/data/flags/normal/br.png'

def mainlist(item):
    idioma2 ="destacadas" 
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Audio Latino", action="submenu",host="http://cinecalidad.com/",thumbnail=thumbmx, extra = "peliculas"))
    itemlist.append( Item(channel=item.channel, title="Audio Castellano", action="submenu",host="http://cinecalidad.com/espana/",thumbnail=thumbes, extra = "peliculas"))
    itemlist.append( Item(channel=item.channel, title="Audio Portugues", action="submenu",host="http://cinemaqualidade.com/",thumbnail=thumbbr, extra ="filmes"))
    return itemlist


def submenu(item):
    idioma='peliculas'
    idioma2 ="destacada"
    host = item.host
    if item.host == "http://cinemaqualidade.com/" : 
       idioma = "filmes"
       idioma2 = "destacado"
    logger.info("pelisalacarta.channels.cinecalidad submenu")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title=idioma.capitalize(), action="peliculas", url=host,thumbnail='https://s31.postimg.org/4g4lytrqj/peliculas.png', fanart='https://s31.postimg.org/4g4lytrqj/peliculas.png'))
    itemlist.append( Item(channel=item.channel, title="Destacadas", action="peliculas", url=host+"/genero-"+idioma+"/"+idioma2+"/", thumbnail='https://s32.postimg.org/wzyinepsl/destacadas.png', fanart='https://s32.postimg.org/wzyinepsl/destacadas.png'))
    itemlist.append( Item(channel=item.channel, title="Generos", action="generos", url=host+"/genero-"+idioma, thumbnail='https://s31.postimg.org/szbr0gmkb/generos.png',fanart='https://s31.postimg.org/szbr0gmkb/generos.png'))   
    itemlist.append( Item(channel=item.channel, title="Por Año", action="anyos", url=host+"/"+idioma+"-por-ano", thumbnail='https://s31.postimg.org/iyl5fvzqz/pora_o.png', fanart='https://s31.postimg.org/iyl5fvzqz/pora_o.png'))
    
    return itemlist



def anyos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a href="([^"]+)">([^<]+)</a> '
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle
        thumbnail = item.thumbnail
        plot = item.plot
        itemlist.append( Item(channel=item.channel, action="peliculas" , title=title , url=url, thumbnail=thumbnail, plot=plot, fanart=item.thumbnail))

    return itemlist

def generos(item):
    tgenero = {"Comedia":"https://s32.postimg.org/q7g2qs90l/comedia.png",
               "Suspenso":"https://s31.postimg.org/kb629gscb/suspenso.png",
               "Drama":"https://s32.postimg.org/e6z83sqzp/drama.png",
               "Acción":"https://s32.postimg.org/4hp7gwh9x/accion.png",
               "Aventura":"https://s32.postimg.org/whwh56is5/aventura.png",
               "Romance":"https://s31.postimg.org/y7vai8dln/romance.png",
               "Fantas\xc3\xada":"https://s32.postimg.org/pklrf01id/fantasia.png",
               "Infantil":"https://s32.postimg.org/i53zwwgsl/infantil.png",
               "Ciencia ficción":"https://s32.postimg.org/6hp3tsxsl/ciencia_ficcion.png",
               "Terror":"https://s32.postimg.org/ca25xg0ed/terror.png",
               "Com\xc3\xa9dia":"https://s32.postimg.org/q7g2qs90l/comedia.png",
               "Suspense":"https://s31.postimg.org/kb629gscb/suspenso.png",
               "A\xc3\xa7\xc3\xa3o":"https://s32.postimg.org/4hp7gwh9x/accion.png",
               "Fantasia":"https://s32.postimg.org/pklrf01id/fantasia.png",
               "Fic\xc3\xa7\xc3\xa3o cient\xc3\xadfica":"https://s32.postimg.org/6hp3tsxsl/ciencia_ficcion.png"}
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li id="menu-item-.*?" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-.*?"><a href="([^"]+)">([^<]+)<\/a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle
        thumbnail = tgenero[scrapedtitle]
        plot = item.plot
        itemlist.append( Item(channel=item.channel, action="peliculas" , title=title , url=url, thumbnail=thumbnail, plot=plot, fanart=item.thumbnail))

    return itemlist

def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
   
    patron = '<div class="home_post_cont.*? post_box">.*?<a href="([^"]+)".*?src="([^"]+)".*?title="(.*?) \((.*?)\)".*?p&gt;([^&]+)&lt;'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle, scrapedyear, scrapedplot  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle+' ('+scrapedyear+')'
        thumbnail = scrapedthumbnail
        plot = scrapedplot
        year = scrapedyear
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, fanart='https://s31.postimg.org/puxmvsi7v/cinecalidad.png', contentTitle = contentTitle, infoLabels={'year':year} ))
    
    try:     
        patron  = "<link rel='next' href='([^']+)' />" 
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Página siguiente >>" , url=next_page[0], fanart='https://s31.postimg.org/puxmvsi7v/cinecalidad.png') )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist


def dec(item):
        link=[]
        val= item.split(' ')
        link = map(int, val)
        for i in range(len(link)):
            link[i] = link[i]-7
            real=''.join(map(chr, link))
        return (real)


def findvideos(item):
    servidor = {"http://uptobox.com/":"uptobox","http://userscloud.com/":"userscloud","https://my.pcloud.com/publink/show?code=":"pcloud","http://thevideos.tv/":"thevideos","http://ul.to/":"uploadedto","http://turbobit.net/":"turbobit","http://www.cinecalidad.com/protect/v.html?i=":"cinecalidad","http://www.mediafire.com/download/":"mediafire","https://www.youtube.com/watch?v=":"youtube","http://thevideos.tv/embed-":"thevideos","//www.youtube.com/embed/":"youtube","http://ok.ru/video/":"okru","http://ok.ru/videoembed/":"okru","http://www.cinemaqualidade.com/protect/v.html?i=":"cinemaqualidade.com","http://usersfiles.com/":"usersfiles","https://depositfiles.com/files/":"depositfiles","http://www.nowvideo.sx/video/":"nowvideo","http://vidbull.com/":"vidbull","http://filescdn.com/":"filescdn","https://www.yourupload.com/watch/":"yourupload"}
    logger.info()
    itemlist=[]
    data = httptools.downloadpage(item.url).data
    
    patron = 'dec\("([^"]+)"\)\+dec\("([^"]+)"\)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    recomendados = ["uptobox","thevideos","nowvideo","pcloud"]
    for scrapedurl,scrapedtitle in matches:
        if dec(scrapedurl) in servidor:

          if 'yourupload' in dec(scrapedurl):
            url = dec(scrapedurl).replace('watch','embed')+dec(scrapedtitle)
          else:
            url = dec(scrapedurl)+dec(scrapedtitle)

          title = "Ver "+item.contentTitle+" en "+servidor[dec(scrapedurl)].upper()
          if (servidor[dec(scrapedurl)]) in recomendados:
            title=title+"[COLOR limegreen] [I] (Recomedado) [/I] [/COLOR]"
          thumbnail = servertools.guess_server_thumbnail(servidor[dec(scrapedurl)])
          plot = ""
          itemlist.append( Item(channel=item.channel, action="play" , title=title ,fulltitle = item.title, url=url, thumbnail=thumbnail, plot=plot,extra=item.thumbnail, server=servidor[dec(scrapedurl)]))
    
    if config.get_library_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la biblioteca[/COLOR]', url=item.url,
                             action="add_pelicula_to_library", extra="findvideos", contentTitle = item.contentTitle))
    return itemlist

def play(item):
    
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
            
    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.extra
        videochannel=item.channel
    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = 'http://www.cinecalidad.to'
        elif categoria == 'infantiles':
            item.url ='http://www.cinecalidad.to/genero-peliculas/infantil/'
        itemlist = peliculas(item)
        if itemlist[-1].title == 'Página siguiente >>':
                itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

