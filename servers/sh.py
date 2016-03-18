# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para longurl (acortador de url)
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re
from core import scrapertools
from core import logger
from core import config
import urllib

DEBUG = config.get_setting("debug")


 
def expand_url(url):
    
    logger.info("[longurl.py] expand_url ")
    url_c=url[7:len(url)]
    long_url=""
    logger.info("[longurl.py] - get_long_urls: " + url)
    longurl_data = scrapertools.downloadpage("http://api.longurl.org/v2/expand?url="+urllib.quote_plus(url_c))
    logger.info(longurl_data)
    long_url = re.findall('<long-url><!\[CDATA\[(.*?)\]\]></long-url>',longurl_data)
                   
    return long_url[0]    
        
            

def test():
    
    location = expand_url("http://sh.st/saBL8")
    ok = ("meuvideos.com" in location)
    print "Funciona:",ok

    return ok