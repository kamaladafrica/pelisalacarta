# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para adnstream
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re

from core import logger
from core import scrapertools
from core import httptools

def get_video_url( page_url , premium = False , user="" , password="" , video_password="" ):
    logger.info("page_url='%s'" % page_url)

    # Saca el código del vídeo
    data = httptools.downloadpage(page_url).data.replace("\\", "")
    video_urls = []
    matches = scrapertools.find_multiple_matches(data, '"label"\s*:\s*(.*?),"type"\s*:\s*"([^"]+)","file"\s*:\s*"([^"]+)"')
    for calidad, tipo, video_url in matches:
        tipo = tipo.replace("video/", "")
        video_urls.append([".%s %sp [tusfiles]" % (tipo, calidad), video_url])
    
    video_urls.sort(key=lambda it:int(it[0].split("p ", 1)[0].rsplit(" ")[1]))
    
    return video_urls
