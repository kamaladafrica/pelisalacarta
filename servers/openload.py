# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector for openload.co
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re

from core import logger
from core import scrapertools

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0',
       'Accept-Encoding': 'none'}


def test_video_exists(page_url):
    logger.info("pelisalacarta.servers.openload test_video_exists(page_url='%s')" % page_url)

    data = scrapertools.downloadpageWithoutCookies(page_url)

    if 'We are sorry!' in data:
        return False, "[Openload] El archivo no existe o ha sido borrado" 

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("pelisalacarta.servers.openload url=" + page_url)
    video_urls = []

    video = True
    data = scrapertools.downloadpageWithoutCookies(page_url)

    if "videocontainer" not in data:
        video = False
        url = page_url.replace("/embed/","/f/")
        data = scrapertools.downloadpageWithoutCookies(url)
        text_encode = scrapertools.get_match(data,"Click to start Download.*?<script[^>]+>(.*?)</script")

    else:
        text_encode = scrapertools.get_match(data,"</div[^<]+<script[^>]+>(.*?)</script>")

    from aadecode import decode as aadecode
    text_decode = aadecode(text_encode)

    subtitle = scrapertools.find_single_match(data, '<track kind="captions" src="([^"]+)" srclang="es"')
    #Header para la descarga
    header_down = "|User-Agent="+headers['User-Agent']+"|"
    if video == True:
        videourl = scrapertools.get_match(text_decode, "(http.*?true)")
        videourl = scrapertools.get_header_from_response(videourl,header_to_get="location")
        videourl = videourl.replace("https://","http://").replace("?mime=true","")
        extension = videourl[-4:]
        video_urls.append([ extension + " [Openload]", videourl+header_down+extension, 0, subtitle])
    else:
        videourl = scrapertools.find_single_match(text_decode, '"href",(?:\s|)\'([^\']+)\'')
        videourl = videourl.replace("https://","http://")
        extension = videourl[-4:]
        video_urls.append([ extension + " [Openload]", videourl+header_down+extension])

    for video_url in video_urls:
        logger.info("pelisalacarta.servers.openload %s - %s" % (video_url[0],video_url[1]))

    return video_urls


# Encuentra vídeos del servidor en el texto pasado
def find_videos(text):
    encontrados = set()
    devuelve = []

    patronvideos = '//(?:www.)?openload.../(?:embed|f)/([0-9a-zA-Z-_]+)'
    logger.info("pelisalacarta.servers.openload find_videos #" + patronvideos + "#")

    matches = re.compile(patronvideos, re.DOTALL).findall(text)

    for media_id in matches:
        titulo = "[Openload]"
        url = 'https://openload.co/embed/%s/' % media_id
        if url not in encontrados:
            logger.info("  url=" + url)
            devuelve.append([titulo, url, 'openload'])
            encontrados.add(url)
        else:
            logger.info("  url duplicada=" + url)

    return devuelve
