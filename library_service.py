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

from core import config
from core import jsontools
from core import logger
from core.item import Item
from platformcode import library

logger.info("pelisalacarta.library_service Actualizando series...")

directorio = library.join_path(config.get_library_path(), "SERIES")
logger.info("directorio="+directorio)

if not library.path_exists(directorio):
    library.make_dir(directorio)

flag = library.check_tvshow_xml()
nombre_fichero_config_canal = library.join_path(config.get_data_path(), library.TVSHOW_FILE)

try:

    if config.get_setting("updatelibrary") == "true":

        data = library.read_file(nombre_fichero_config_canal)
        dict_data = jsontools.load_json(data)

        for tvshow_id in dict_data.keys():
            logger.info("pelisalacarta.library_service serie="+dict_data[tvshow_id]["name"])

            itemlist = []

            for channel in dict_data[tvshow_id]["channels"].keys():
                carpeta = "{0} [{1}]".format(library.title_to_filename(
                    dict_data[tvshow_id]["channels"][channel]["tvshow"].lower()), channel)
                # carpeta = dict_serie[tvshow_id]["channels"][channel]["path"]
                ruta = library.join_path(config.get_library_path(), "SERIES", carpeta)
                logger.info("pelisalacarta.library_service ruta =#"+ruta+"#")

                if flag:
                    library.make_dir(ruta)

                if library.path_exists(ruta):
                    logger.info("pelisalacarta.library_service Actualizando "+carpeta)
                    logger.info("pelisalacarta.library_service url "+dict_data[tvshow_id]["channels"][channel]["url"])

                    item = Item(url=dict_data[tvshow_id]["channels"][channel]["url"],
                                show=(dict_data[tvshow_id]["channels"][channel]["tvshow"]))

                    try:
                        pathchannels = library.join_path(config.get_runtime_path(), 'channels', channel + '.py')
                        logger.info("pelisalacarta.library_service Cargando canal  " + pathchannels + " " + channel)
                        obj = imp.load_source(channel, pathchannels)
                        itemlist = obj.episodios(item)

                    except:
                        import traceback
                        logger.error(traceback.format_exc())
                        itemlist = []
                else:
                    logger.info("pelisalacarta.library_service No actualiza {0} (no existe el directorio)".
                                format(dict_data[tvshow_id]["name"]))
                    itemlist = []

                library.savelibrary_tvshow(itemlist[0], itemlist, flag)

        library.update()
    else:
        logger.info("No actualiza la biblioteca, está desactivado en la configuración de pelisalacarta")

except:
    logger.info("pelisalacarta.library_service No hay series para actualizar")
