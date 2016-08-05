# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector for openload.co
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re

from core import config
from core import logger
from core import scrapertools


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0'}


def test_video_exists(page_url):
    logger.info("pelisalacarta.servers.openload test_video_exists(page_url='%s')" % page_url)

    data = scrapertools.downloadpageWithoutCookies(page_url)

    if 'We are sorry!' in data:
        return False, "[Openload] El archivo no existe o ha sido borrado" 

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("pelisalacarta.servers.openload url=" + page_url)
    video_urls = []

    data = scrapertools.downloadpageWithoutCookies(page_url)
    subtitle = scrapertools.find_single_match(data, '<track kind="captions" src="([^"]+)" srclang="es"')
    #Header para la descarga
    header_down = "|User-Agent="+headers['User-Agent']+"|"

    try:
        from lib.aadecode import decode as aadecode
        if "videocontainer" not in data:
            url = page_url.replace("/embed/","/f/")
            data = scrapertools.downloadpageWithoutCookies(url)
            text_encode = scrapertools.find_single_match(data,"Click to start Download.*?<script[^>]+>(.*?)</script")
            text_decode = aadecode(text_encode)

            videourl = "http://" + scrapertools.find_single_match(text_decode, '(openload.co/.*?)\}')
            if videourl == "http://":
                videourl = decodeopenload(data)
            extension = scrapertools.find_single_match(data, '<meta name="description" content="([^"]+)"')
            extension = "." + extension.rsplit(".", 1)[1]
            video_urls.append([extension + " [Openload]", videourl+header_down+extension])
        else:
            text_encode = scrapertools.find_multiple_matches(data,'<script[^>]+>(ﾟωﾟ.*?)</script>')
            decodeindex = aadecode(text_encode[0])
            subtract = scrapertools.find_single_match(decodeindex, 'welikekodi.*?(\([^;]+\))')
            if subtract:
                index = int(eval(subtract))
                # Buscamos la variable que nos indica el script correcto
                text_decode = aadecode(text_encode[index])
                videourl = "http://" + scrapertools.find_single_match(text_decode, "(openload.co/.*?)\}")
                extension = "." + scrapertools.find_single_match(text_decode, "video/(\w+)")
            else:
                videourl = decodeopenload(data)
                extension = "." + scrapertools.find_single_match(decodeindex, "video/(\w+)")
    except:
        import traceback
        logger.info("pelisalacarta.servers.openload "+traceback.format_exc())
        
        # Falla el método, se utiliza la api aunque en horas punta no funciona
        from core import jsontools
        file_id = scrapertools.find_single_match(page_url, 'embed/([0-9a-zA-Z-_]+)')
        login = "97b2326d7db81f0f"
        key = "AQFO3QJQ"
        data = scrapertools.downloadpageWithoutCookies("https://api.openload.co/1/file/dlticket?file=%s&login=%s&key=%s" % (file_id, login, key))
        data = jsontools.load_json(data)
        if data["status"] == 200:
            ticket = data["result"]["ticket"]
            data = scrapertools.downloadpageWithoutCookies("https://api.openload.co/1/file/dl?file=%s&ticket=%s" % (file_id, ticket))
            data = jsontools.load_json(data)
            extension = "." + scrapertools.find_single_match(data["result"]["content_type"], '/(\w+)')
            videourl = data['result']['url'] + '?mime=true'

    if config.get_platform() != "plex":
        video_urls.append([extension + " [Openload] ", videourl+header_down+extension, 0, subtitle])
    else:
        video_urls.append([extension + " [Openload] ", videourl, 0, subtitle])

    for video_url in video_urls:
        logger.info("pelisalacarta.servers.openload %s - %s" % (video_url[0],video_url[1]))

    return video_urls


# Encuentra vídeos del servidor en el texto pasado
def find_videos(text):
    encontrados = set()
    devuelve = []

    patronvideos = '(?:openload|oload).../(?:embed|f)/([0-9a-zA-Z-_]+)'
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


#Code take from plugin IPTVPlayer: https://gitlab.com/iptvplayer-for-e2/iptvplayer-for-e2/
#Thanks to samsamsam for his work
def decodeopenload(data):
    import base64, math
    from lib.png import Reader as PNGReader
    # get image data
    imageData = scrapertools.find_single_match(data, '<img *id="linkimg" *src="([^"]+)"')

    imageData = base64.b64decode(imageData.rsplit('base64,', 1)[1])
    x, y, pixel, meta = PNGReader(bytes=imageData).read()

    imageStr = ""
    try:
        for item in pixel:
            for p in item:
                imageStr += chr(p)
    except:
        pass

    # split image data
    imageTabs = []
    i = -1
    for idx in range(len(imageStr)):
        if imageStr[idx] == '\0':
            break
        if 0 == (idx % (12 * 20)):
            imageTabs.append([])
            i += 1
            j = -1
        if 0 == (idx % (20)):
            imageTabs[i].append([])
            j += 1
        imageTabs[i][j].append(imageStr[idx])

    # get signature data
    scripts = scrapertools.find_multiple_matches(data, '<script src="(/assets/js/obfuscator/[^"]+)"')
    for scr in scripts:
        data = scrapertools.downloadpageWithoutCookies('https://openload.co%s' % scr)
        if "signatureNumbers" in data:
            break
    signStr = scrapertools.find_single_match(data, '[\'"]([^"\']+)[\'"]')

    # split signature data
    signTabs = []
    i = -1
    for idx in range(len(signStr)):
        if signStr[idx] == '\0':
            break
        if 0 == (idx % (11 * 26)):
            signTabs.append([])
            i += 1
            j = -1
        if 0 == (idx % (26)):
            signTabs[i].append([])
            j += 1
        signTabs[i][j].append(signStr[idx])

    # get link data
    linkData = {}
    for i in [2, 3, 5, 7]:
        linkData[i] = []
        tmp = ord('c')
        for j in range(len(signTabs[i])):
            for k in range(len(signTabs[i][j])):
                if tmp > 122:
                    tmp = ord('b')
                if signTabs[i][j][k] == chr(int(math.floor(tmp))):
                    if len(linkData[i]) > j:
                        continue
                    tmp += 2.5;
                    if k < len(imageTabs[i][j]):
                        linkData[i].append(imageTabs[i][j][k])
    res = []
    for idx in linkData:
        res.append(''.join(linkData[idx]).replace(',', ''))

    res = res[3] + '~' + res[1] + '~' + res[2] + '~' + res[0]
    videourl = 'http://openload.co/stream/{0}?mime=true'.format(res)
    
    return videourl
