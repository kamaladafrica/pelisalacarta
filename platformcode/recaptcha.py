# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import re
import xbmc
import xbmcgui

from core import config
from core import httptools
from core import scrapertools
from platformcode import platformtools

resultado = []


def start(key, version, referer):
    global resultado
    headers = {'Referer': referer,
               'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0; WOW64; Trident/4.0; SLCC1)'}
    params = "k=%s&hl=es&v=%s&t=2&ff=true" % (key, version)
    url = "https://www.google.com/recaptcha/api/fallback?%s" % params
    data = httptools.downloadpage(url, headers=headers, replace_headers=True).data

    mensaje = scrapertools.find_single_match(data, '<div class="rc-imageselect-desc-no-canonical">(.*?)(?:</label>|</div>)')
    mensaje = unicode(scrapertools.htmlclean(mensaje), "utf-8")
    token = scrapertools.find_single_match(data, 'name="c" value="([^"]+)"')
    headers["Referer"] = url
    while True:
        params2 = "k=%s&c=%s" % (key, token)
        imagen = "https://www.google.com/recaptcha/api2/payload?%s" % params2

        mainWindow = Recaptcha('Recaptcha.xml', config.get_runtime_path(), imagen=imagen, mensaje=mensaje)
        mainWindow.doModal()

        post = "c=%s" % token
        if resultado is None:
            return None

        for r in resultado:
            post += "&response=%s" % r

        data = httptools.downloadpage(url, post, headers=headers, replace_headers=True).data
        result = scrapertools.find_single_match(data, '<div class="fbc-verification-token">.*?>([^<]+)<')
        if not result:
            mensaje = scrapertools.find_single_match(data, '<div class="rc-imageselect-desc-no-canonical">(.*?)(?:</label>|</div>)')
            mensaje = unicode(scrapertools.htmlclean(mensaje), "utf-8")
            token = scrapertools.find_single_match(data, 'name="c" value="([^"]+)"')
        else:
            platformtools.dialog_notification("Captcha Correcto", "La verificación ha concluido")
            return result


class Recaptcha(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        self.mensaje = kwargs.get("mensaje")
        self.imagen = kwargs.get("imagen")

    def onInit(self):
        global resultado
        self.botones = {}
        for i in range(10005, 10014):
            self.botones[i] = 0

        self.setCoordinateResolution(2)
        self.getControl(10020).setImage(self.imagen)
        self.getControl(10000).setLabel(self.mensaje)
        self.setFocusId(10005)


    def onClick(self, control):
        global resultado
        if control == 10003:
            resultado = None
            self.close()
        elif control == 10004:
            resultado = []
            self.close()
        elif control == 10002:
            for k, v in self.botones.items():
                if v == 1:
                    resultado.append(k - 10005)
            self.close()
        else:
            if self.botones.get(control) == 0:
                self.botones[control] = 1
            else:
                self.botones[control] = 0
