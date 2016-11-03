# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para powvideo
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re

from core import jsunpack
from core import logger
from core import scrapertools

headers = [['User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0']]


def test_video_exists( page_url ):
    logger.info("pelisalacarta.servers.powvideo test_video_exists(page_url='%s')" % page_url)
    
    data = scrapertools.cache_page(page_url)
    #if "File Not Found" in data: return False, "[powvideo] El archivo no existe o ha sido borrado"
    
    return True,""


def get_video_url( page_url , premium = False , user="" , password="", video_password="" ):
    logger.info("pelisalacarta.servers.powvideo get_video_url(page_url='%s')" % page_url)

    url = page_url.replace("http://powvideo.net/","http://powvideo.net/iframe-") + "-640x360.html"     
    headers.append(['Referer',url.replace("iframe","embed")])
    
    data = scrapertools.cache_page(url, headers=headers)

    # Extrae la URL
    data = scrapertools.find_single_match(data,"<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    data = jsunpack.unpack(data).replace("\\","")

    data = scrapertools.find_single_match(data,"sources\=\[([^\]]+)\]")
    logger.info("data="+data)

    matches = scrapertools.find_multiple_matches(data, "src:'([^']+)'")
    
    rtmp = scrapertools.find_single_match(data, "'(rtmp://[^']+)'")
    mp4 = scrapertools.find_single_match(data, "'(http://[^']+\.mp4)'")
    if rtmp:
      m3u8_file = rtmp.split("?")[0].split("/")[-1].replace("_n",".m3u8")
    
    fake_id = mp4.split("/")[3]
    id = mp4.split("/")[3][1:]
    
    video_urls = []
    
    mp4_url = mp4.replace(fake_id,id) 
    
    
    if rtmp:
      rtmp = rtmp.replace(fake_id,id)
      rtmp, playpath = rtmp.split("mp4:",1)
      rtmp_url = "%s playpath=%s swfUrl=http://powvideo.net/player6/jwplayer.flash.swf pageUrl=%s" % (rtmp, "mp4:"+playpath, page_url)

      m3u8_url = mp4_url.replace("v.mp4", m3u8_file)
      
      video_urls.append(["rtmp [powvideo]", rtmp_url])
      video_urls.append([".m3u8 [powvideo]", m3u8_url])
      
    video_urls.append([".mp4  [powvideo]", mp4_url])
    
    for video_url in video_urls:
        logger.info("pelisalacarta.servers.powvideo %s - %s" % (video_url[0],video_url[1]))

    return video_urls


# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    # http://powvideo.net/sbb9ptsfqca2
    # http://powvideo.net/embed-sbb9ptsfqca2
    # http://powvideo.net/iframe-sbb9ptsfqca2
    # http://powvideo.net/preview-sbb9ptsfqca2
    patronvideos  = 'powvideo.net/(?:embed-|iframe-|preview-|)([a-z0-9]+)'
    logger.info("pelisalacarta.servers.powvideo find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[powvideo]"
        url = "http://powvideo.net/"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'powvideo' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
            
    return devuelve
