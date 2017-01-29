# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para yaske-netutv, netutv, hqqtv waawtv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re
import urllib

from core import jsontools
from core import httptools
from core import logger
from core import scrapertools


def get_video_url(page_url, premium = False, user="", password="", video_password=""):
    logger.info(" url="+page_url)

    id_video = page_url.rsplit("=", 1)[1]
    page_url_hqq = "http://hqq.tv/player/embed_player.php?vid=%s&autoplay=no" % id_video
    data_page_url_hqq = httptools.downloadpage(page_url_hqq, add_referer=True).data

    data_unwise = unwise_process(data_page_url_hqq).replace("\\", "")
    at = scrapertools.find_single_match(data_unwise, 'var at\s*=\s*"([^"]+)"')

    url = "http://hqq.tv/sec/player/embed_player.php?iss=&vid=%s&at=%s&autoplayed=yes&referer=on" \
          "&http_referer=&pass=&embed_from=&need_captcha=0" % (id_video, at)
    data_player = httptools.downloadpage(url, add_referer=True).data
    data_unescape = scrapertools.find_multiple_matches(data_player, 'document.write\(unescape\("([^"]+)"')
    data = ""
    for d in data_unescape:
        data += urllib.unquote(d)

    vars_data = scrapertools.find_single_match(data, '/player/get_md5.php",\s*\{(.*?)\}')
    matches = scrapertools.find_multiple_matches(vars_data, '\s*([^:]+):\s*([^,]*)[,"]')
    params = {}
    for key, value in matches:
        if key == "adb":
            params[key] = "1"
        elif '"' in value:
            params[key] = value.replace('"', '')
        else:
            value_var = scrapertools.find_single_match(data, 'var\s*%s\s*=\s*"([^"]+)"' % value)
            params[key] = value_var

    params = urllib.urlencode(params)
    head = {'X-Requested-With': 'XMLHttpRequest'}
    data = httptools.downloadpage("http://hqq.tv/player/get_md5.php?" + params, headers=head).data

    media_urls = []
    url_data = jsontools.load_json(data)
    if url_data["html5_file"].startswith("#"):
        media_url = tb(url_data["html5_file"][1:])
    else:
        media_url = tb(url_data["html5_file"])

    video_urls = []
    media = media_url + "|User-Agent=Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X)"
    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:]+" Opción 1 [netu.tv]", media])
    media = media.replace('secip/1', 'secip/1/')
    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:]+" Opción 2 [netu.tv]", media])

    for video_url in video_urls:
        logger.info(" %s - %s" % (video_url[0],video_url[1]))

    return video_urls


## Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    ## Patrones
    # http://www.yaske.net/archivos/netu/tv/embed_54b15d2d41641.html
    # http://www.yaske.net/archivos/netu/tv/embed_54b15d2d41641.html?1
    # http://hqq.tv/player/embed_player.php?vid=498OYGN19D65&autoplay=no
    # http://hqq.tv/watch_video.php?v=498OYGN19D65
    # http://netu.tv/player/embed_player.php?vid=82U4BRSOB4UU&autoplay=no
    # http://netu.tv/watch_video.php?v=96WDAAA71A8K
    # http://waaw.tv/player/embed_player.php?vid=82U4BRSOB4UU&autoplay=no
    # http://waaw.tv/watch_video.php?v=96WDAAA71A8K
    patterns = [
        '/netu/tv/embed_(.*?$)',
        'hqq.tv/[^=]+=([a-zA-Z0-9]+)',
        'netu.tv/[^=]+=([a-zA-Z0-9]+)',
        'waaw.tv/[^=]+=([a-zA-Z0-9]+)',
        'netu.php\?nt=([a-zA-Z0-9]+)'
    ]

    url = "http://netu.tv/watch_video.php?v=%s"
    for pattern in patterns:
        logger.info(" #"+pattern+"#")
        matches = re.compile(pattern,re.DOTALL).findall(data)

        for match in matches:
            titulo = "[netu.tv]"
            url = url % match
            if url not in encontrados:
                logger.info("  url="+url)
                devuelve.append( [ titulo , url , 'netutv' ] )
                encontrados.add(url)
                break
            else:
                logger.info("  url duplicada="+url)

    return devuelve


## Obtener la url del m3u8
def tb(b_m3u8_2):
    j = 0
    s2 = ""
    while j < len(b_m3u8_2):
        s2+= "\\u0"+b_m3u8_2[j:(j+3)]
        j+= 3

    return s2.decode('unicode-escape').encode('ASCII', 'ignore')

## --------------------------------------------------------------------------------
## --------------------------------------------------------------------------------

def unwise1(w):
    int1 = 0
    result = ""
    while int1 < len(w):
        result = result + chr(int(w[int1:int1 + 2], 36))
        int1 += 2
    return result

def logblock(s):
    if len(s)>12:
        return "("+str(len(s))+") "+s[0:5]+"..."+s[-5:]
    else:
        return "("+str(len(s))+") "+s

def unwise(w, i, s, e, wi, ii, si, ei):
    int1 = 0
    int2 = 0
    int3 = 0
    int4 = 0
    string1 = ""
    string2 = ""
    while True:
        if w != "":
            if int1 < wi:
                string2 = string2 + w[int1:int1+1]
            elif int1 < len(w):
                string1 = string1 + w[int1:int1+1]
            int1 += 1
        if i != "":
            if int2 < ii:
                string2 = string2 + i[int2:int2+1]
            elif int2 < len(i):
                string1 = string1 + i[int2:int2+1]
            int2 += 1
        if s != "":
            if int3 < si:
                string2 = string2 + s[int3:int3+1]
            elif int3 < len(s):
                string1 = string1 + s[int3:int3+1]
            int3 = int3 + 1
        if e != "":
            if int4 < ei:
                string2 = string2 + e[int4:int4+1]
            elif int4 < len(e):
                string1 = string1 + e[int4:int4+1]
            int4 = int4 + 1
        if len(w) + len(i) + len(s) + len(e) == len(string1) + len(string2):
            break

    int1 = 0
    int2 = 0
    result = ""
    contador = 0
    while int1 < len(string1):
        flag = -1
        if ord(string2[int2:int2+1]) % 2:
            flag = 1
        anadir = chr(int(string1[int1:int1+2], 36) - flag)

        result = result + anadir
        int2 += 1
        if int2 >= len(string2):
            int2 = 0
        int1 += 2
        contador = contador + 1

    return result

def unwise_process(result):
    while True:
        a = re.compile(r';?eval\s*\(\s*function\s*\(\s*w\s*,\s*i\s*,\s*s\s*,\s*e\s*\).+?[\"\']\s*\)\s*\)(?:\s*;)?').search(result)
        if not a:
            break
        a = a.group()
        tmp = re.compile(r'\}\s*\(\s*[\"\'](\w*)[\"\']\s*,\s*[\"\'](\w*)[\"\']\s*,\s*[\"\'](\w*)[\"\']\s*,\s*[\"\'](\w*)[\"\']').search(a)
        if not tmp:
            result = result.replace(a, "")
        else:
            wise = ["", "", "", ""]
            wise = tmp.groups()
            if a.find("while") == -1:
                result = result.replace(a, unwise1(wise[0]))
            else:
                c = 0
                wisestr = ["", "", "", ""]
                wiseint = [0, 0, 0, 0]
                b = re.compile(r'while(.+?)var\s*\w+\s*=\s*\w+\.join\(\s*[\"\'][\"\']\s*\)').search(a).group(1)
                for d in re.compile(r'if\s*\(\s*\w*\s*\<\s*(\d+)\)\s*\w+\.push').findall(b):
                    wisestr[c] = wise[c]
                    wiseint[c] = int(d)
                    c += 1
                result = result.replace(a, unwise(wisestr[0], wisestr[1], wisestr[2], wisestr[3], wiseint[0], wiseint[1], wiseint[2], wiseint[3]))
    return result
