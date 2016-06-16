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
    data = scrapertools.downloadpage("https://real-debrid.com/downloader", headers=headers.items())
    
    # Se busca el script que contiene el token para la api
    matchjs = scrapertools.find_single_match(data, '<script type="text/javascript">(eval\(function\(r,e,a,l.*?)</script>')
    if matchjs != "":
        while not re.search(r'var tokenBearer', matchjs, re.DOTALL):
            matchjs = unpack(matchjs)
        token_auth = scrapertools.find_single_match(matchjs, "tokenBearer='([^']+)'")
    
    headers.pop('Cookie', None)
    headers['Authorization'] = "Bearer %s" % token_auth
    post = {'link' : page_url, 'password' : video_password}
    url = 'https://api.real-debrid.com/rest/1.0/unrestrict/link'
    data = requests.post(url, data=post, headers=headers).text
    data = jsontools.load_json(data)

    itemlist = []
    if 'download' in data:
        return data['download'].encode('utf-8')
    else:
        if 'error' in data:
            msg = data['error'].decode('utf-8','ignore')
            msg = msg.replace("hoster_unavailable", "Servidor no disponible") \
                     .replace("unavailable_file", "Archivo no disponible")
            server_error = "REAL-DEBRID: " + msg
            return server_error
        else:
            return "REAL-DEBRID: No se ha generado ningún enlace"


def unpack(texto):
    patron = "bearer.join\(''\)\;\}\('(.*)','(.*)','(.*)','(.*)'"
    r, e, a, l = re.search(patron, texto, re.DOTALL).groups()
    x = 0
    y = 0
    z = 0
    t = ""
    token = ""
    while True:
        if x < 5:
            token += r[x]
        elif x < len(r):
            t += r[x]
        x += 1
        if y < 5:
            token += e[y]
        elif y < len(e):
            t += e[y]
        y += 1
        if z < 5:
            token += a[z]
        elif z < len(a):
            t += a[z]
        z += 1
        
        if (len(r) + len(e) + len(a) + len(l)) == (len(t) + len(token) + len(l)):
            break

    y = 0
    bearer = ""
    for i in range(0, len(t), 2):
        c = -1
        if ord(token[y]) % 2:
            c = 1
        bearer += chr(int(t[i:i+2], 32) - c)
        y += 1
        if y >= len(token):
            y= 0

    return bearer
