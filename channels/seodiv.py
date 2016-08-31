# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canal (seodiv) por Hernan_Ar_c
# ------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys


from core import logger
from core import config
from core import scrapertools
from core.item import Item
from core import servertools

__channel__ = "seodiv"
__category__ = "S"
__type__ = "generic"
__title__ = "seodiv"
__language__ = "ES"

DEBUG = config.get_setting("debug")

host='http://www.seodiv.com'

def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.channels.seodiv mainlist")

    itemlist = []
    

    itemlist.append( Item(channel=__channel__, title="Todos", action="todas", url=host,thumbnail='https://s32.postimg.org/544rx8n51/series.png', fanart='https://s32.postimg.org/544rx8n51/series.png'))
   
    return itemlist

def todas(item):

    logger.info("pelisalacarta.channels.seodiv todas")
    itemlist = []
    data = scrapertools.cache_page(item.url)
    
    patron ='<\/div><img src="([^"]+)".*?\/>.*?'
    patron+='<div class="title-topic">([^<]+)<\/div>.*?'
    patron +='<div class="sh-topic">([^<]+)<\/div><\/a>.*?'
    patron +='<div class="read-more-top"><a href="([^"]+)" style='
       
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail, scrapedtitle, scrapedplot, scrapedurl in matches: 
        url = host+scrapedurl
        title = scrapedtitle.decode('utf-8')
        thumbnail = scrapedthumbnail
        fanart = 'https://s32.postimg.org/gh8lhbkb9/seodiv.png'
        plot = scrapedplot
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"])")
        itemlist.append( Item(channel=__channel__, action="temporadas" ,title=title , url=url, thumbnail=thumbnail, fanart=fanart, plot= plot ))
           

    return itemlist

    
def search(item,texto):
    logger.info("metaserie.py search")
    texto = texto.replace(" ","+")
    item.url = item.url+texto

    if texto!='':
        return todas(item)
    else:
        return []
        
def categorias(item):
    logger.info("pelisalacarta.channels.seodiv categoias")
    itemlist = []
    data = scrapertools.cache_page(item.url)
    patron ="<a href='([^']+)' class='tag-link-.*? tag-link-position-.*?' title='.*?' style='font-size: 11px;'>([^<]+)<\/a>" 
    
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
	url = scrapedurl
	title = scrapedtitle
	if (DEBUG): logger.info("title=["+title+"], url=["+url+"])")
	itemlist.append( Item(channel=__channel__, action="todas" , title=title, fulltitle=item.fulltitle, url=url))
        
    return itemlist            
        
def temporadas(item):
    logger.info("pelisalacarta.channels.seodiv temporadas")
    itemlist = []
    data = scrapertools.cache_page(item.url)
    url_base= item.url
    patron = '<a class="collapsed" data-toggle="collapse" data-parent="#accordion" href=.*? aria-expanded="false" aria-controls=.*?>([^<]+)<\/a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    temp=1
    if 'Temporada' in str(matches):
	for scrapedtitle in matches:
	   url = url_base
	   title = scrapedtitle
	   thumbnail = item.thumbnail
	   plot = item.plot
	   fanart = scrapertools.find_single_match(data,'<img src="([^"]+)"/>.*?</a>')
	   if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"])")
	   itemlist.append( Item(channel=__channel__, action="episodios" , title=title , fulltitle=item.title, url=url, thumbnail=thumbnail, plot=plot, fanart = fanart, temp=str(temp)))
           temp = temp+1 
        return itemlist
    else:
       return episodios(item)

def episodios(item):
    
    logger.info("pelisalacarta.channels.seodiv episodios")
    itemlist = []
    data = scrapertools.cache_page(item.url)
    tempo = item.title
    if 'Temporada'in item.title:
        item.title = item.title.replace('Temporada', 'temporada')
        item.title = item.title.strip()
        item.title = item.title.replace(' ','-')
                
    patron ='<li><a href="([^"]+)">Capitulo ([^<]+)<\/a><\/li>'
    
        
    matches = re.compile(patron,re.DOTALL).findall(data)
    idioma = scrapertools.find_single_match(data,' <p><span class="ah-lead-tit">Idioma:</span>&nbsp;<span id="l-vipusk">([^<]+)</span></p>')
    
    for scrapedurl, scrapedtitle in matches:
        url = host+scrapedurl
	title = ' Capitulo '+scrapedtitle+' ('+idioma+')'
	thumbnail = item.thumbnail
	plot = item.plot
	fanart=''
	if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"])")
	if str(item.title) in scrapedurl or 'temporada'not in str(item.title):
           itemlist.append( Item(channel=__channel__, action="findvideos" , title=title, fulltitle=item.fulltitle, url=url, thumbnail=item.thumbnail, plot=plot))
        
    return itemlist            
                                 
    


    
