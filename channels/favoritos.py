# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta 4
# Copyright 2015 tvalacarta@gmail.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# This file is part of pelisalacarta 4.
#
# pelisalacarta 4 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pelisalacarta 4 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pelisalacarta 4.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------------------
# Lista de vídeos favoritos
# ------------------------------------------------------------

import os
import time

from core import config
from core import filetools
from core import logger
from core.item import Item
from platformcode import platformtools


def mainlist(item):
    logger.info("pelisalacarta.core.favoritos mainlist")
    itemlist = []
    bookmarkpath = config.get_setting("bookmarkpath")

    for fichero in sorted(filetools.listdir(bookmarkpath)):
        if fichero.endswith(".json"):

            item = Item().fromjson(filetools.read(filetools.join(bookmarkpath, fichero)))
            if item.action == "play":
                item.channel = "favoritos"

            item.path = filetools.join(bookmarkpath, fichero)
            itemlist.append(item)
    return itemlist


def savebookmark(item):
    logger.info("pelisalacarta.core.favoritos savebookmark")
    bookmarkpath = config.get_setting("bookmarkpath")

    # Si se llega aqui mediante el menu contextual, hay que recuperar los parametros action y channel
    if item.from_action:
        item.__dict__["action"] = item.__dict__.pop("from_action")
    if item.from_channel:
        item.__dict__["channel"] = item.__dict__.pop("from_channel")

    # Elegimos el nombre
    title = item.contentTitle
    if not title:
        title = item.fulltitle
    if not title:
        title = item.title

    item.title = platformtools.dialog_input(title + " [" + item.channel + "]")
    if item.title is None:
        return

    # Graba el fichero
    filename = filetools.join(bookmarkpath, str(time.time()) + ".json")
    filetools.write(filename, item.tojson())

    platformtools.dialog_ok(config.get_localized_string(30102), item.title,
                            config.get_localized_string(30108))  # 'se ha añadido a favoritos'


def deletebookmark(item):
    logger.info("pelisalacarta.core.favoritos deletebookmark")
    filetools.remove(item.path)
    platformtools.itemlist_refresh()


##################################################
# Funciones para migrar favoritos antiguos (.txt)
def readbookmark(filename, readpath=config.get_setting("bookmarkpath")):
    logger.info("[favoritos.py] readbookmark")
    import urllib

    if readpath.lower().startswith("smb://"):
        from lib.sambatools import libsmb as samba
        bookmarkfile = samba.get_file_handle_for_reading(filename, readpath)
    else:
        filepath = os.path.join(readpath, filename)

        # Lee el fichero de configuracion
        logger.info("[favoritos.py] filepath=" + filepath)
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

    # Campos fulltitle y canal añadidos
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


def check_bookmark(savepath):
    # Crea un listado con las entradas de favoritos

    for fichero in sorted(filetools.listdir(savepath)):
        # Ficheros antiguos (".txt")
        if fichero.endswith(".txt"):
            # Esperamos 0.1 segundos entre ficheros, para que no se solapen los nombres de archivo
            time.sleep(0.1)

            # Obtenemos el item desde el .txt
            canal, titulo, thumbnail, plot, server, url, fulltitle = readbookmark(fichero)
            if canal == "":
                canal = "favoritos"
            item = Item(channel=canal, action="play", url=url, server=server, title=fulltitle, thumbnail=thumbnail,
                        plot=plot, fanart=thumbnail, extra=os.path.join(savepath, fichero), fulltitle=fulltitle,
                        folder=False)

            # Eliminamos el .txt
            filetools.remove(item.extra)
            item.extra = ""

            # Graba el nuevo fichero
            filename = filetools.join(savepath, str(time.time()) + ".json")
            filetools.write(filename, item.tojson())

check_bookmark(config.get_setting("bookmarkpath"))
