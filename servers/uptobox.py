# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para uptobox
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urllib,re

from core import scrapertools
from core import logger

def test_video_exists( page_url ):
    logger.info("[uptobox.py] test_video_exists(page_url='%s')" % page_url)

    data = scrapertools.cache_page(page_url)

    if "Streaming link:" in data: return True,""
    wait = scrapertools.find_single_match(data, "You have to wait ([0-9]+) (minute|second)")
    if len(wait)>0:
        tiempo = wait[1].replace("minute","minuto/s").replace("second","segundos")
        return False, "[Uptobox] Alcanzado límite de descarga.<br/>Tiempo de espera: "+wait[0]+" "+tiempo

    return True,""

def get_video_url( page_url , premium = False , user="" , password="", video_password="" ):
    logger.info("[uptobox.py] get_video_url(page_url='%s')" % page_url)
    #Si el enlace es directo de upstream
    if "uptobox" not in page_url:
        data = scrapertools.cache_page(url)
        patron = "<source src='//([^']+)' type='([^']+)'"
        media = scrapertools.find_single_match(data, patron)
        media_url = "http://"+media[0]
        extension = media[1]
    else:
        data = scrapertools.cache_page(page_url)
        #Si el archivo tiene enlace de streaming se redirige a upstream
        if "Streaming link:" in data:
            url = "http://uptostream.com/iframe/"+scrapertools.find_single_match(page_url,'uptobox.com/([a-z0-9]+)')
            data = scrapertools.cache_page(url)
            patron = "<source src='//([^']+)' type='([^']+)'"
            media = scrapertools.find_single_match(data, patron)
            media_url = "http://"+media[0]
            extension = media[1]
        else:
            #Si no lo tiene se utiliza la descarga normal
            post = ""
            matches = scrapertools.find_multiple_matches(data, '<input type="hidden".*?name="([^"]+)".*?value="([^"]*)">')
            for inputname, inputvalue in matches:
                post += inputname + "=" + inputvalue + "&"

            data = scrapertools.cache_page( page_url , post=post)
            media = scrapertools.find_single_match(data, '<!--DOWNLOAD BUTTON-->[\s\S]+<a href="([^"]+)">')
            #Solo es necesario codificar la ultima parte de la url
            url_strip = urllib.quote(media.rsplit('/', 1)[1])
            media_url = media.rsplit('/', 1)[0] +"/"+url_strip
            extension = media_url[-4:]

    video_urls = []
    video_urls.append( [ extension+" [uptobox]", media_url])

    for video_url in video_urls:
        logger.info("[uptobox.py] %s - %s" % (video_url[0],video_url[1]))
    return video_urls

# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    # http://uptobox.com/q7asuktfr84x
	# http://uptostream.com/q7asuktfr84x
	# http://uptostream.com/iframe/q7asuktfr84x
    patronvideos  = '(?:uptobox|uptostream).com(?:/iframe/|/)([a-z0-9]+)'
    logger.info("[uptobox.py] find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[uptobox]"
        if "uptostream" in data:
            url = "http://uptostream.com/iframe/"+match
        else:
            url = "http://uptobox.com/"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'uptobox' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    return devuelve
