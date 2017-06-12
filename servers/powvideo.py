# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para powvideo
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re

from core import httptools
from core import logger
from core import scrapertools
from lib import jsunpack

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0']]
host = "http://powvideo.net/"


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "<title>watch </title>" in data.lower():
        return False, "[powvideo] El archivo no existe o  ha sido borrado"
    if "el archivo ha sido borrado por no respetar" in data.lower():
        return False, "[powvideo] El archivo no existe o ha sido borrado por no respetar los Terminos de uso"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    url = page_url.replace(host, "http://powvideo.xyz/iframe-") + "-954x562.html"

    data = httptools.downloadpage(page_url).data
    id = scrapertools.find_single_match(data, 'name="id" value="([^"]+)"')
    fname = scrapertools.find_single_match(data, 'name="fname" value="([^"]+)"')
    hash = scrapertools.find_single_match(data, 'name="hash" value="([^"]+)"')
    post = "op=download1&usr_login=&referer=&fname=%s&id=%s&hash=%s&imhuman=Proceed+to+video" % (fname, id, hash)

    data = httptools.downloadpage(page_url, post, headers={'Referer': page_url, "X-Requested-With": "XMLHttpRequest"}).data

    matches = None
    i = 0
    while not matches:
        matches = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
        data = httptools.downloadpage(page_url, post, headers={'Referer': page_url, "X-Requested-With": "XMLHttpRequest"}).data
        i += 1
        if i > 5:
            break

    data = jsunpack.unpack(matches).replace("\\", "")

    data = scrapertools.find_single_match(data.replace('"', "'"), "sources\s*=[^\[]*\[([^\]]+)\]")
    matches = scrapertools.find_multiple_matches(data, "[src|file]:'([^']+)'")
    video_urls = []
    for video_url in matches:
        _hash = scrapertools.find_single_match(video_url, '[A-z0-9\_\-]{40,}')
        hash = decrypt(_hash)
        video_url = video_url.replace(_hash, hash)

        filename = scrapertools.get_filename_from_url(video_url)[-4:]
        if video_url.startswith("rtmp"):
            rtmp, playpath = video_url.split("vod/", 1)
            video_url = "%svod/ playpath=%s swfUrl=%splayer6/jwplayer.flash.swf pageUrl=%s" % \
                        (rtmp, playpath, host, page_url)
            filename = "RTMP"
        elif video_url.endswith(".m3u8"):
            video_url += "|User-Agent=" + headers[0][1]
        elif video_url.endswith("/v.mp4"):
            video_url_flv = re.sub(r'/v.mp4\|', '/v.flv|', video_url)
            video_urls.append(["flv [powvideo]", video_url_flv])

        video_urls.append([filename + " [powvideo]", video_url])

    video_urls.sort(key=lambda x: x[0], reverse=True)
    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls


# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []

    # http://powvideo.net/sbb9ptsfqca2
    # http://powvideo.net/embed-sbb9ptsfqca2
    # http://powvideo.net/iframe-sbb9ptsfqca2
    # http://powvideo.net/preview-sbb9ptsfqca2
    patronvideos = 'powvideo.net/(?:embed-|iframe-|preview-|)([a-z0-9]+)'
    logger.info("#" + patronvideos + "#")
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    for match in matches:
        titulo = "[powvideo]"
        url = "http://powvideo.net/" + match
        if url not in encontrados:
            logger.info("  url=" + url)
            devuelve.append([titulo, url, 'powvideo'])
            encontrados.add(url)
        else:
            logger.info("  url duplicada=" + url)

    return devuelve


def decrypt(h):
    import base64

    if len(h) % 4:
        h += "="*(4-len(h) % 4)
    sig = []
    h = base64.b64decode(h.replace("-", "+").replace("_", "/"))
    for c in range(len(h)):
        sig += [ord(h[c])]

    k = "powvideoembedz"
    sec = []
    for c in range(len(k)):
        sec += [ord(k[c])]

    dig = range(256)
    g = 0
    v = 128
    for b in range(len(sec)):
        a = (v + (sec[b] & 15)) % 256
        c = dig[(g)]
        dig[g] = dig[a]
        dig[a] = c
        g += 1

        a = (v + (sec[b] >> 4 & 15)) % 256
        c = dig[g]
        dig[g] = dig[a]
        dig[a] = c
        g += 1

    k = 0
    q = 1
    p = 0
    n = 0
    for b in range(512):
        k = (k + q) % 256
        n = (p + dig[(n + dig[k]) % 256]) % 256
        p = (k + p + dig[n]) % 256
        c = dig[k]
        dig[k] = dig[n]
        dig[n] = c

    q = 3
    for a in range(v):
        b = 255 - a
        if dig[a] > dig[b]:
            c = dig[a]
            dig[a] = dig[b]
            dig[b] = c

    k = 0
    for b in range(512):
        k = (k + q) % 256
        n = (p + dig[(n + dig[k]) % 256]) % 256
        p = (k + p + dig[n]) % 256
        c = dig[k]
        dig[k] = dig[n]
        dig[n] = c

    q = 5
    for a in range(v):
        b = 255 - a
        if dig[a] > dig[b]:
            c = dig[a]
            dig[a] = dig[b]
            dig[b] = c

    k = 0
    for b in range(512):
        k = (k + q) % 256
        n = (p + dig[(n + dig[k]) % 256]) % 256
        p = (k + p + dig[n]) % 256
        c = dig[k]
        dig[k] = dig[n]
        dig[n] = c

    q = 7
    k = 0
    u = 0
    d = []
    for b in range(len(dig)):
        k = (k + q) % 256
        n = (p + dig[(n + dig[k]) % 256]) % 256
        p = (k + p + dig[n]) % 256
        c = dig[k]
        dig[k] = dig[n]
        dig[n] = c
        u = dig[(n + dig[(k + dig[(u + p) % 256]) % 256]) % 256]
        d += [u]

    c = []
    for f in range(len(d)):
        try: c += [(256 + (sig[f] - d[f])) % 256]
        except: break

    h = ""
    for s in c:
      h += chr(s)

    return h
