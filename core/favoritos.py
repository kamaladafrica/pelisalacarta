# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Lista de v�deos favoritos
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import os
import sys
import urllib

from lib.samba import libsmb as samba

import config
import logger
from item import Item

CHANNELNAME = "favoritos"
DEBUG = True
BOOKMARK_PATH = config.get_setting("bookmarkpath")

if not samba.usingsamba(BOOKMARK_PATH):
    if BOOKMARK_PATH == "":
        BOOKMARK_PATH = os.path.join(config.get_data_path(), "bookmarks")
    if not os.path.exists(BOOKMARK_PATH):
        logger.debug("[favoritos.py] Path de bookmarks no existe, se crea: "+BOOKMARK_PATH)
        os.mkdir(BOOKMARK_PATH)

logger.info("[favoritos.py] path="+BOOKMARK_PATH)


def isGeneric():
    return True


def mainlist(item):
    logger.info("[favoritos.py] mainlist")
    itemlist = []

    # Crea un listado con las entradas de favoritos
    if samba.usingsamba(BOOKMARK_PATH):
        ficheros = samba.get_files(BOOKMARK_PATH)
    else:
        ficheros = os.listdir(BOOKMARK_PATH)
    
    # Ordena el listado por nombre de fichero (orden de incorporaci�n)
    ficheros.sort()
    
    # Rellena el listado
    for fichero in ficheros:

        try:
            # Lee el bookmark
            canal, titulo, thumbnail, plot, server, url, fulltitle = readbookmark(fichero)
            if canal == "":
                canal = "favoritos"

            # Crea la entrada
            # En extra va el nombre del fichero para poder borrarlo
            # <-- A�ado fulltitle con el titulo de la peli
            itemlist.append(Item(channel=canal, action="play", url=url, server=server, title=fulltitle,
                                 thumbnail=thumbnail, plot=plot, fanart=thumbnail,
                                 extra=os.path.join(BOOKMARK_PATH, fichero), fulltitle=fulltitle, folder=False))
        except:
            for line in sys.exc_info():
                logger.error("%s" % line)
    
    return itemlist


def readbookmark(filename, readpath=BOOKMARK_PATH):
    logger.info("[favoritos.py] readbookmark")

    if samba.usingsamba(readpath):
        bookmarkfile = samba.get_file_handle_for_reading(filename, readpath)
    else:
        filepath = os.path.join(readpath, filename)

        # Lee el fichero de configuracion
        logger.info("[favoritos.py] filepath="+filepath)
        bookmarkfile = open(filepath)
    lines = bookmarkfile.readlines()

    try:
        titulo = urllib.unquote_plus(lines[0].strip())
    except:
        titulo = lines[0].strip()
    
    try:
        url = urllib.unquote_plus(lines[1].strip())
    except:
        url = lines[1].strip()
    
    try:
        thumbnail = urllib.unquote_plus(lines[2].strip())
    except:
        thumbnail = lines[2].strip()
    
    try:
        server = urllib.unquote_plus(lines[3].strip())
    except:
        server = lines[3].strip()
        
    try:
        plot = urllib.unquote_plus(lines[4].strip())
    except:
        plot = lines[4].strip()

    # Campos fulltitle y canal a�adidos
    if len(lines) >= 6:
        try:
            fulltitle = urllib.unquote_plus(lines[5].strip())
        except:
            fulltitle = lines[5].strip()
    else:
        fulltitle = titulo

    if len(lines) >= 7:
        try:
            canal = urllib.unquote_plus(lines[6].strip())
        except:
            canal = lines[6].strip()
    else:
        canal = ""

    bookmarkfile.close()

    return canal, titulo, thumbnail, plot, server, url, fulltitle


def savebookmark(canal=CHANNELNAME, titulo="", url="", thumbnail="", server="", plot="", fulltitle="",
                 savepath=BOOKMARK_PATH):
    logger.info("[favoritos.py] savebookmark(path="+savepath+")")

    # Crea el directorio de favoritos si no existe
    if not samba.usingsamba(savepath):
        try:
            os.mkdir(savepath)
        except:
            pass

    # Lee todos los ficheros
    if samba.usingsamba(savepath):
        ficheros = samba.get_files(savepath)
    else:
        ficheros = os.listdir(savepath)
    ficheros.sort()
    
    # Averigua el �ltimo n�mero
    if len(ficheros) > 0:
        # XRJ: Linea problem�tica, sustituida por el bucle siguiente
        # filenumber = int( ficheros[len(ficheros)-1][0:-4] )+1
        filenumber = 1
        for fichero in ficheros:
            logger.info("[favoritos.py] fichero="+fichero)
            try:
                tmpfilenumber = int(fichero[0:8])+1
                if tmpfilenumber > filenumber:
                    filenumber = tmpfilenumber
            except:
                pass
    else:
        filenumber = 1

    # Genera el contenido
    filecontent = ""
    filecontent = filecontent + urllib.quote_plus(titulo)+'\n'
    filecontent = filecontent + urllib.quote_plus(url)+'\n'
    filecontent = filecontent + urllib.quote_plus(thumbnail)+'\n'
    filecontent = filecontent + urllib.quote_plus(server)+'\n'
    filecontent = filecontent + urllib.quote_plus(plot)+'\n'
    filecontent = filecontent + urllib.quote_plus(fulltitle)+'\n'
    filecontent = filecontent + urllib.quote_plus(canal)+'\n'

    # Genera el nombre de fichero
    from core import scrapertools
    filename = '%08d-%s.txt' % (filenumber, scrapertools.slugify(fulltitle))
    logger.info("[favoritos.py] savebookmark filename="+filename)

    # Graba el fichero
    if not samba.usingsamba(savepath):
        fullfilename = os.path.join(savepath, filename)
        bookmarkfile = open(fullfilename, "w")
        bookmarkfile.write(filecontent)
        bookmarkfile.flush()
        bookmarkfile.close()
    else:
        samba.store_File(filename, filecontent, savepath)


def deletebookmark(fullfilename, deletepath=BOOKMARK_PATH):
    logger.info("[favoritos.py] deletebookmark(fullfilename="+fullfilename+",deletepath="+deletepath+")")

    if not samba.usingsamba(deletepath):
        os.remove(os.path.join(urllib.unquote_plus(deletepath), urllib.unquote_plus(fullfilename)))
    else:
        fullfilename = fullfilename.replace("\\", "/")
        partes = fullfilename.split("/")
        filename = partes[len(partes)-1]
        logger.info("[favoritos.py] filename="+filename)
        logger.info("[favoritos.py] deletepath="+deletepath)
        samba.delete_files(filename, deletepath)
