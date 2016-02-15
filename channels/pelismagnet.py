# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para pelismagnet
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re

from core import scrapertools
from core.item import Item

from core import jsontools

__channel__ = "pelismagnet"
__category__ = "F,S,D"
__type__ = "generic"
__title__ = "Pelis Magnet"
__language__ = "ES"

host = 'http://pelismag.net'
api = host + '/api'

def isGeneric():
    return True

def mainlist(item):

    itemlist = []
    itemlist.append( Item(channel=__channel__, action="obtenirpelis", title="Estrenos", url=api + "?sort_by=date_added&page=0"))
    itemlist.append( Item(channel=__channel__, action="obtenirpelis", title="+ Populares", url=api + "?page=0"))
    itemlist.append( Item(channel=__channel__, action="obtenirpelis", title="+ Valoradas", url=api + "?sort_by=rating&page=0"))
    itemlist.append( Item(channel=__channel__, action="search" , title="Buscar...", url=api + "?keywords=%s&page=0"))
    return itemlist

def obtenirpelis(item):
    itemlist = []
    data = scrapertools.cachePage(item.url)
    List = jsontools.load_json(data)

    for i in List:
        title = i['nom']
        try:
            if i['magnets']['M1080']['magnet'] != None:
                url = i['magnets']['M1080']['magnet']
            else:
                url = i['magnets']['M720']['magnet']
        except:
            try:
                url = i['magnets']['M720']['magnet']
            except:
                return [Item(channel=__channel__, title='No hay enlace magnet disponible para esta pelicula')]
        try:
            thumbnail = 'http://image.tmdb.org/t/p/w342' + i['posterurl']
        except:
            thumbnail = 'No disponible'
        plot = i['info']
        itemlist.append( Item(channel=__channel__, action="play", title=title , url=url, server="torrent", thumbnail=thumbnail , plot=plot , folder=False) )
        if len(itemlist) == 0:
            itemlist.append( Item(channel=__channel__, action="obtenirpelis", title="Fin de lista", folder=False) )
        elif len(itemlist) == 50:
            url = re.sub(
                r'page=(\d+)',
                r'page=' + str( int( re.search('\d+', item.url).group() ) + 1 ),
                item.url
            )
            itemlist.append( Item(channel=__channel__, action="obtenirpelis", title=">> Página siguiente" , url=url) )

    return itemlist

def search(item,texto):
    item.url = item.url % texto.replace(' ','%20')
    return obtenirpelis(item)
