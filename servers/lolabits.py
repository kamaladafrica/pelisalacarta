# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para lolabits
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urllib,re

from core import scrapertools
from core import logger

def test_video_exists( page_url ):
    logger.info("[lolabits.py] test_video_exists(page_url='%s')" % page_url)

    data = scrapertools.cache_page(page_url)

    fileId = scrapertools.find_single_match(data,'<input.*?name="FileId" value="([^"]+)"')
    if len(fileId) == 0:
        return False, "[Lolabits] El archivo no existe o ha sido borrado" 

    return True,""

def get_video_url( page_url , premium = False , user="" , password="", video_password="" ):
    logger.info("[lolabits.py] get_video_url(page_url='%s')" % page_url)

    data = scrapertools.cache_page(page_url)
    #Parámetros post: token y fileId
    token = scrapertools.find_single_match(data,'<input.*?name="__RequestVerificationToken".*?value="([^"]+)"')
    fileId = scrapertools.find_single_match(data,'<input.*?name="FileId" value="([^"]+)"')
    post = "fileId="+fileId+"&__RequestVerificationToken="+urllib.quote(token)
    #URL para extrar dirección de descarga según servidor
    if "http://abelhas.pt" in page_url: url_download = "http://abelhas.pt/action/License/Download"
    else: url_download = "http://lolabits.es/action/License/Download"
    data = scrapertools.downloadpage(url_download , post=post)
    media_url = scrapertools.find_single_match(data,'"redirectUrl":"([^"]+)"')
    media_url = media_url.decode("unicode-escape")
    #Sacar header para el nombre del archivo
    try:
        content = scrapertools.get_header_from_response(media_url, header_to_get="content-disposition")
        extension = scrapertools.find_single_match(content, 'filename="([^"]+)"')[-4:]
    except:
        extension = page_url.rsplit('.',1)[1]

    video_urls = []
    video_urls.append( [ extension+" [lolabits]", media_url])

    for video_url in video_urls:
        logger.info("[lolabits.py] %s - %s" % (video_url[0],video_url[1]))
    return video_urls

# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    # http://lolabits.es/example/example.mp4(video)
    # http://abelhas.pt/example/example.mp4(video)
    patronvideos  = '(lolabits.es.*|abelhas.pt.*)'
    logger.info("[lolabits.py] find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[lolabits]"
        url = "http://"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'lolabits' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    return devuelve