# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector for openload.co
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re
from core import scrapertools
from core import logger
from core import config

           
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0',
       'Accept-Encoding': 'none'}


def test_video_exists(page_url):
    logger.info("[openload.py] test_video_exists(page_url='%s')" % page_url)

    data = scrapertools.downloadpageWithoutCookies(page_url)

    if 'We are sorry!' in data:
        return False, 'File Not Found or Removed.'

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("[openload.py] url=" + page_url)
    video_urls = []

    data = scrapertools.downloadpageWithoutCookies(page_url)

    if "videocontainer" not in data:
        url = page_url.replace("/embed/","/f/")
        data = scrapertools.downloadpageWithoutCookies(url)
        url, extension = decode(data, video=False)
        video_urls.append([str(extension) + " [Openload]", url])          
    else:
        url, extension = decode(data)
        video_urls.append([str(extension) + " [Openload]", url])

    return video_urls

def decode(data, video=True):
    if video == True:
        text_encode = scrapertools.get_match(data,"<video[^<]+<script[^>]+>(.*?)</script>")
    else:
        text_encode = scrapertools.get_match(data,"Click to start Download.*?<script[^>]+>(.*?)</script")
    
    text = re.sub(r"\s+", "", text_encode)
    text = text \
        .replace("(ﾟДﾟ)[ﾟoﾟ]","|") \
        .replace("((ﾟｰﾟ)+(ﾟｰﾟ)+(ﾟΘﾟ))", "9") \
        .replace("((ﾟｰﾟ)+(ﾟｰﾟ))", "8") \
        .replace("((ﾟｰﾟ)+(o^_^o))", "7") \
        .replace("((o^_^o)+(o^_^o))", "6") \
        .replace("((ﾟｰﾟ)+(ﾟΘﾟ))", "5") \
        .replace("(ﾟｰﾟ)", "4") \
        .replace("((o^_^o)-(ﾟΘﾟ))", "2") \
        .replace("(o^_^o)", "3") \
        .replace("(ﾟΘﾟ)", "1") \
        .replace("(c^_^o)", "0") \
        .replace("(ﾟДﾟ)[ﾟεﾟ]", ",") \
        .replace("(3+3+0)", "6") \
        .replace("(3-1+0)", "2") \
        .replace("(!+[]+!+[])", "2") \
        .replace("(-~-~2)", "4") \
        .replace("(-~-~1)", "3") \
        .replace("(+!+[])", "1") \
        .replace("(0+0)", "0")
    text = re.sub(r"\+", "", text).split('|')[2]

    for n in text[1:].split(','):
        text = text.replace(',%s' % n, chr(int(n, 8)))

    #Header para la descarga
    header_down = "|User-Agent="+headers['User-Agent']+"|"
    if video == True:
        videourl = scrapertools.find_single_match(text, "vr='([^']+)'")
        videourl = scrapertools.get_header_from_response(videourl,header_to_get="location")
        videourl = videourl.replace("https://","http://").replace("?mime=true","")
        extension = videourl[-4:]
        return videourl+header_down+extension, extension
    else:
        videourl = scrapertools.find_single_match(text, '"href", \'([^\']+)\'')
        videourl = videourl.replace("https://","http://")
        extension = videourl[-4:]
        return videourl+header_down+extension, extension

# Encuentra vídeos del servidor en el texto pasado
def find_videos(text):
    encontrados = set()
    devuelve = []

    patronvideos = '//(?:www.)?openload.../(?:embed|f)/([0-9a-zA-Z-_]+)'
    logger.info("[openload.py] find_videos #" + patronvideos + "#")

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