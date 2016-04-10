# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector for videowood.tv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# by DrZ3r0
# ------------------------------------------------------------

import re

from core import scrapertools
from core import logger
from core import jsunpack


def test_video_exists(page_url):
    logger.info("pelisalacarta.servers.videowood test_video_exists(page_url='%s')" % page_url)

    data = scrapertools.cache_page(page_url)

    if "This video doesn't exist." in data:
        return False, 'The requested video was not found.'

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("pelisalacarta.servers.videowood url=" + page_url)
    video_urls = []

    data = scrapertools.cache_page(page_url)
    text_encode = scrapertools.find_single_match(data, "(ﾟωﾟ.*?)</script>")
    text_decode = decode(text_encode)

    # URL del vídeo
    patron = "'([^']+)'"
    media_url = scrapertools.find_single_match(text_decode, patron)

    video_urls.append([media_url[-4:] + " [Videowood]", media_url])

    return video_urls

def decode(text):
    text = re.sub(r"\s+", "", text)
    data = text.split("+(ﾟДﾟ)[ﾟoﾟ]")[0]
    chars = data.split("+(ﾟДﾟ)[ﾟεﾟ]+")[1:]

    txt = ""
    for char in chars:
        char = char \
            .replace("(oﾟｰﾟo)","u") \
            .replace("c", "0") \
            .replace("(ﾟДﾟ)['0']", "c") \
            .replace("ﾟΘﾟ", "1") \
            .replace("!+[]", "1") \
            .replace("-~", "1+") \
            .replace("o", "3") \
            .replace("_", "3") \
            .replace("ﾟｰﾟ", "4") \
            .replace("(+", "(")
        char = re.sub(r'\((\d)\)', r'\1', char)
        c = ""; subchar = ""
        for v in char:
            c+= v
            try: x = c; subchar+= str(eval(x)); c = ""
            except: pass
        txt+= subchar + "|"
    txt = txt[:-1].replace('+','')
    txt_result = "".join([ chr(int(n, 8)) for n in txt.split('|') ])

    return txt_result
        

# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    patronvideos = r"https?://(?:www.)?videowood.tv/(?:embed/|video/)[0-9a-z]+"
    logger.info("pelisalacarta.servers.videowood find_videos #" + patronvideos + "#")

    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    for url in matches:
        titulo = "[Videowood]"
        url = url.replace('/video/', '/embed/')
        if url not in encontrados:
            logger.info("  url=" + url)
            devuelve.append([titulo, url, 'videowood'])
            encontrados.add(url)
        else:
            logger.info("  url duplicada=" + url)

    return devuelve