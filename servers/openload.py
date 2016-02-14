# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector for openload.co
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re, urllib2, cookielib, os
from core import scrapertools
from core import logger
from core import config

           
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

ficherocookies = os.path.join( config.get_data_path(), 'cookies.dat' )
cj = cookielib.MozillaCookieJar()
urlopen = urllib2.urlopen
Request = urllib2.Request


if cj != None:
    if os.path.isfile(ficherocookies):
        cj.load(ficherocookies)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
else:
    opener = urllib2.build_opener()

urllib2.install_opener(opener)


def test_video_exists(page_url):
    logger.info("[openload.py] test_video_exists(page_url='%s')" % page_url)

    req = Request(page_url, '', headers)
    response = urlopen(req, timeout=60)
    data = response.read()

    if 'We are sorry!' in data:
        return False, 'File Not Found or Removed.'

    return True, ""


def decodeOpenLoad(html, video=True):
    if video == True:
        aastring = re.search(r"<video(?:.|\s)*?<script\s[^>]*?>((?:.|\s)*?)</script", html, re.DOTALL | re.IGNORECASE).group(1)
    else:
        aastring = re.search(r"Click to start Download(?:.|\s).*?<script\s[^>]*?>((?:.|\s)*?)</script", html, re.DOTALL | re.IGNORECASE).group(1)
    
    aastring = aastring.replace("((ﾟｰﾟ) + (ﾟｰﾟ) + (ﾟΘﾟ))", "9")
    aastring = aastring.replace("((ﾟｰﾟ) + (ﾟｰﾟ))","8")
    aastring = aastring.replace("((ﾟｰﾟ) + (o^_^o))","7")
    aastring = aastring.replace("((o^_^o) +(o^_^o))","6")
    aastring = aastring.replace("((ﾟｰﾟ) + (ﾟΘﾟ))","5")
    aastring = aastring.replace("(ﾟｰﾟ)","4")
    aastring = aastring.replace("((o^_^o) - (ﾟΘﾟ))","2")
    aastring = aastring.replace("(o^_^o)","3")
    aastring = aastring.replace("(ﾟΘﾟ)","1")
    aastring = aastring.replace("(c^_^o)","0")
    aastring = aastring.replace("(ﾟДﾟ)[ﾟεﾟ]","\\")
    aastring = aastring.replace("(3 +3 +0)","6")
    aastring = aastring.replace("(3 - 1 +0)","2")
    aastring = aastring.replace("(!+[]+!+[])","2")
    aastring = aastring.replace("(-~-~2)","4")
    aastring = aastring.replace("(-~-~1)","3")
    aastring = aastring.replace("(+!+[])","1")
    aastring = aastring.replace("(0+0)","0")

    decodestring = re.search(r"\\\+([^(]+)", aastring, re.DOTALL | re.IGNORECASE).group(1)
    decodestring = "\\+"+ decodestring
    decodestring = decodestring.replace("+","")
    decodestring = decodestring.replace(" ","")
    
    decodestring = decode(decodestring)
    decodestring = decodestring.replace("\\/","/")

    #Header para la descarga
    header_down = "|User-Agent="+headers['User-Agent']+"|"
    if video == True:
        videourl = re.search(r"vr='([^']+)'", decodestring, re.DOTALL | re.IGNORECASE).group(1)
        videourl = scrapertools.get_header_from_response(videourl,header_to_get="location")
        videourl = videourl.replace("https://","http://").replace("?mime=true","")
        extension = videourl[-4:]
        return videourl+header_down+extension, extension
    else:
        videourl = re.search(r'"href", \'([^\']+)\'', decodestring, re.DOTALL | re.IGNORECASE).group(1)
        videourl = videourl.replace("https://","http://")
        extension = videourl[-4:]
        return videourl+header_down+extension, extension

def decode(encoded):
    for octc in (c for c in re.findall(r'\\(\d{2,3})', encoded)):
        encoded = encoded.replace(r'\%s' % octc, chr(int(octc, 8)))
    return encoded.decode('utf8')


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("[openload.py] url=" + page_url)
    video_urls = []
    req = Request(page_url, '', headers)
    response = urlopen(req, timeout=60)
    data = response.read()
    if "videocontainer" not in data:
        url = page_url.replace("/embed/","/f/")
        req = Request(url, '', headers)
        response = urlopen(req, timeout=60)
        data = response.read()
        cj.save(ficherocookies)
        response.close()
        url, extension = decodeOpenLoad(data, video=False)
        video_urls.append([str(extension) + " [Openload]", url])          
    else:
        cj.save(ficherocookies)
        response.close()
        url, extension = decodeOpenLoad(data)
        video_urls.append([str(extension) + " [Openload]", url])

    return video_urls


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