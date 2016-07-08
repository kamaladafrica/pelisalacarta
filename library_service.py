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
# ------------------------------------------------------------
# Service for updating new episodes on library series
# ------------------------------------------------------------

import imp
import math

from core import config
from core import filetools
from core import logger
from core.item import Item
from platformcode import library
from platformcode import platformtools


def main():
    logger.info("pelisalacarta.library_service Actualizando series...")
    logger.info("library path ="+library.TVSHOWS_PATH)

    if not filetools.exists(library.TVSHOWS_PATH):
        filetools.mkdir(library.TVSHOWS_PATH)

    library.check_tvshow_xml()

    p_dialog = None

    try:

        if config.get_setting("updatelibrary") == "true":

            show_list = []
            # TODO cambiar por filetools
            for path, folders, files in filetools.walk(library.TVSHOWS_PATH):
                show_list.extend([filetools.join(path, f) for f in files if f == "tvshow.json"])
            logger.info("hola holita")
            heading = "Actualizando biblioteca...."
            p_dialog = platformtools.dialog_progress_bg("pelisalacarta", heading)
            p_dialog.update(0, '')
            # fix float porque la division se hace mal en python 2.x
            t = float(100) / len(show_list)

            for i, tvshow_file in enumerate(show_list):

                serie = Item().fromjson(filetools.read(tvshow_file))

                logger.info("pelisalacarta.library_service serie: " + serie.show)
                logger.info("pelisalacarta.library_service url: " + serie.url)
                p_dialog.update(int(math.ceil(i * t)), heading, serie.show)

                # si la serie esta activa se actualiza
                if serie.active:

                    try:
                        pathchannels = filetools.join(config.get_runtime_path(), "channels", serie.channel + '.py')
                        logger.info("pelisalacarta.library_service Cargando canal: " + pathchannels + " " +
                                    serie.channel)

                        obj = imp.load_source(serie.channel, pathchannels)
                        itemlist = obj.episodios(serie)

                        try:
                            library.save_library_tvshow(serie, itemlist)
                        except Exception as ex:
                            logger.info("pelisalacarta.library_service Error al guardar los capitulos de la serie")
                            template = "An exception of type {0} occured. Arguments:\n{1!r}"
                            message = template.format(type(ex).__name__, ex.args)
                            logger.info(message)

                    except Exception as ex:
                        logger.error("Error al obtener los episodios de: {0}".
                                     format(serie.show))
                        template = "An exception of type {0} occured. Arguments:\n{1!r}"
                        message = template.format(type(ex).__name__, ex.args)
                        logger.info(message)

            p_dialog.close()
            # TODO pendiente de arreglar
            # library.update()

        else:
            logger.info("No actualiza la biblioteca, está desactivado en la configuración de pelisalacarta")

    except Exception as ex:
        logger.info("pelisalacarta.library_service Se ha producido un error al actualizar las series")
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logger.info(message)

        if p_dialog:
            p_dialog.close()

if __name__ == "__main__":
    main()
