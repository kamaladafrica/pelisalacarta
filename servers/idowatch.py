# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para idowatch
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os

from core import scrapertools
from core import logger
from core import config
from core import jsunpack

def test_video_exists( page_url ):
    logger.info("pelisalacarta.idowatch test_video_exists(page_url='%s')" % page_url)
    return True,""

def get_video_url( page_url , premium = False , user="" , password="", video_password="" ):
    logger.info("pelisalacarta.idowatch get_video_url(page_url='%s')" % page_url)

    data = scrapertools.cache_page(page_url)

    #file:"http://163.172.7.14/ejvzymzne2gn6devhtlycoglaont3md4cn45tfo7tmyvcrobpf5r66t7sckq/v.mp4",label:"SD"
    patron = 'file:"([^"]+)",label:"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    video_urls = []
    for mediaurl,label in matches:
        video_urls.append( [ scrapertools.get_filename_from_url(mediaurl)[-4:]+" "+label+" [idowatch]",mediaurl])

    for video_url in video_urls:
        logger.info("[idowatch.py] %s - %s" % (video_url[0],video_url[1]))

    return video_urls

# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    # http://idowatch.net/m5k9s1g7il01.html
    patronvideos  = 'idowatch.net/([a-z0-9]+)'
    logger.info("pelisalacarta.idowatch find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[idowatch]"
        url = "http://idowatch.net/"+match+".html"
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'idowatch' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    return devuelve

def test():
    video_urls = get_video_url("http://idowatch.net/m5k9s1g7il01.html")

    return len(video_urls)>0