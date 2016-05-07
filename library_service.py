# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta 4
# Copyright 2015 tvalacarta@gmail.com
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
# ------------------------------------------------------------
# Service for updating new episodes on library series
# ------------------------------------------------------------

import imp
import os

import xbmc

from core import config
from core import jsontools
from core import logger
from core.item import Item
from platformcode import library

logger.info("pelisalacarta.library_service Actualizando series...")

directorio = os.path.join(config.get_library_path(), "SERIES")
logger.info("directorio="+directorio)

if not os.path.exists(directorio):
    os.mkdir(directorio)

library.check_tvshow_xml()
nombre_fichero_config_canal = os.path.join(config.get_data_path(), library.TVSHOW_FILE)

try:

    if config.get_setting("updatelibrary") == "true":

        data = library.read_file(nombre_fichero_config_canal)
        dict_data = jsontools.load_json(data)

        for channel in dict_data.keys():
            logger.info("pelisalacarta.library_service_json canal="+channel)

            itemlist = []

            for tvshow in dict_data.get(channel).keys():
                logger.info("pelisalacarta.library_service serie="+tvshow)

                ruta = os.path.join(config.get_library_path(), "SERIES", tvshow)
                logger.info("pelisalacarta.library_service ruta =#"+ruta+"#")
                if os.path.exists(ruta):
                    logger.info("pelisalacarta.library_service Actualizando "+tvshow)
                    logger.info("pelisalacarta.library_service url "+dict_data.get(channel).get(tvshow))

                    item = Item(url=dict_data.get(channel).get(tvshow), show=tvshow)
                    try:
                        pathchannels = os.path.join(config.get_runtime_path(), 'channels', channel + '.py')
                        logger.info("pelisalacarta.library_service Cargando canal  " + pathchannels + " " + channel)
                        obj = imp.load_source(channel, pathchannels)
                        itemlist = obj.episodios(item)

                    except:
                        import traceback
                        logger.error(traceback.format_exc())
                        itemlist = []
                else:
                    logger.info("pelisalacarta.library_service No actualiza " + tvshow + " (no existe el directorio)")
                    itemlist = []

                for item in itemlist:
                    try:
                        item.show = tvshow
                        new_item = item.clone(action="play_from_library", category="Series")
                        logger.info("new item {}".format(new_item.tostring()))
                        library.savelibrary(new_item)
                    except:
                        logger.info("pelisalacarta.library_service Capitulo no valido")

        import xbmc
        xbmc.executebuiltin('UpdateLibrary(video)')
    else:
        logger.info("No actualiza la biblioteca, está desactivado en la configuración de pelisalacarta")

except:
    logger.info("pelisalacarta.library_service No hay series para actualizar")
