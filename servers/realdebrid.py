# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Real_Debrid
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re
import requests
import time
import urllib

from core import config
from core import jsontools
from core import logger
from core import scrapertools


headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
           'Accept' : 'application/json, text/javascript, */*; q=0.01',
           'Accept-Language' : 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
           'Accept-Encoding' : 'gzip, deflate, br',
           'Connection' : 'keep-alive',
           'Referer' : 'https://real-debrid.com/',
           'Cookie' : 'cookie_accept=y; https=1; lang=es;',
           'X-Requested-With' : 'XMLHttpRequest'}

# Returns an array of possible video url's from the page_url
def get_video_url( page_url , premium = False , user="" , password="", video_password="" ):
    logger.info("pelisalacarta.servers.realdebrid get_video_url( page_url='%s' , user='%s' , password='%s', video_password=%s)"
                % (page_url , user , "**************************"[0:len(password)] , video_password))

    # Hace el login y consigue la cookie
    params = urllib.urlencode([('user', user), ('pass', password), ('pin_challenge', ''),
                               ('pin_answer', 'PIN: 0000'), ('time', int(time.time())) ])
    login_url = 'https://real-debrid.com/ajax/login.php?%s' % params
    
    data = requests.get(login_url, headers=headers).text
    data = jsontools.load_json(data)
    if 'error' in data and data['error'] == 0:
        logger.info("pelisalacarta.servers.realdebrid Se ha logueado correctamente")
        cookie_auth = data['cookie']
    else:
        error_message = data['message'].decode('utf-8','ignore')
        if error_message != "":
            server_error = "REAL-DEBRID: " + error_message
        else:
            server_error = "REAL-DEBRID: Ha ocurrido un error con tu login"

        return server_error

    headers['Cookie'] = headers['Cookie'] + cookie_auth 
    params = urllib.urlencode([('link', page_url), ('pass', video_password),
                               ('remote', '0'), ('time', int(time.time())) ])
    url = 'https://real-debrid.com/ajax/unrestrict.php?%s' % params
    data = requests.get(url, headers=headers).text
    data = jsontools.load_json(data)

    if 'main_link' in data:
        return data['main_link'].encode('utf-8')
    else:
        if 'message' in data:
            msg = data['message'].decode('utf-8','ignore')
            server_error = "REAL-DEBRID: " + msg
            return server_error
        else:
            return "REAL-DEBRID: No se ha generado ningún enlace"
