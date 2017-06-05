# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para rapidvideo
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re
import urllib

from core import httptools
from core import logger
from core import scrapertools


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    try:
        response = httptools.downloadpage(page_url)
    except:
        pass

    if not response.data or "urlopen error [Errno 1]" in str(response.code):
        return False, "[Rapidvideo] Este conector solo funciona a partir de Kodi 17"
    
    if "Object not found" in response.data:
        return False, "[Rapidvideo] El archivo no existe o ha sido borrado"
    
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    urls = scrapertools.find_multiple_matches(data, '"file":"([^"]+)","label":"[^"]*","res":"([^"]+)"')
    for mediaurl, res in urls:
        ext = scrapertools.get_filename_from_url(mediaurl)[-4:]
        video_urls.append(['%s %sp [rapidvideo]' % (ext, res), mediaurl.replace("\\", "")])
    
    return video_urls


# Encuentra vídeos de este servidor en el texto pasado
def find_videos(text):
    encontrados = set()
    devuelve = []
            
    #http://www.rapidvideo.com/e/YK7A0L7FU3A
    patronvideos = 'rapidvideo.(?:org|com)/(?:\?v=|e/|embed/)([A-z0-9]+)'
    logger.info("#" + patronvideos + "#")
    matches = re.compile(patronvideos, re.DOTALL).findall(text)

    for match in matches:
        titulo = "[rapidvideo]"
        url = "https://www.rapidvideo.com/e/" + match
        if url not in encontrados:
            logger.info("  url=" + url)
            devuelve.append([titulo, url, 'rapidvideo'])
            encontrados.add(url)
        else:
            logger.info("  url duplicada=" + url)


    return devuelve
