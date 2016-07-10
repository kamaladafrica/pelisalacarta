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
import re

from core import config
from core import filetools
from core import jsontools
from core import logger
from core.item import Item
from platformcode import library
from platformcode import platformtools


def create_tvshows_from_json():
    logger.info("pelisalacarta.platformcode.library convert_xml_to_json")
    fname = filetools.join(config.get_data_path(), library.TVSHOW_FILE)

    if filetools.exists(fname):
        platformtools.dialog_ok("Biblioteca: Se va a actualizar al nuevo formato",
                                "Seleccione el nombre correcto de cada serie, si no está seguro pulse 'Cancelar'.",
                                "Hay nuevas opciones en 'Biblioteca' y en la 'configuración' del addon.")
        try:
            data = jsontools.loads(filetools.read(fname))
            for tvshow in data:
                for channel in data[tvshow]["channels"]:

                    serie = Item(contentSerieName=data[tvshow]["channels"][channel]["tvshow"],
                                 url=data[tvshow]["channels"][channel]["url"], channel=channel, action="episodios",
                                 title=data[tvshow]["name"])
                    if not tvshow.startswith("t_"):
                        serie.infoLabels["tmdb_id"] = tvshow
                    library.save_library_tvshow(serie, list())

            filetools.rename(fname, "series.json.old")

        except EnvironmentError:
            logger.info("ERROR al leer el archivo: {0}".format(fname))


def create_tvshows_from_xml():
    logger.info("pelisalacarta.platformcode.library convert_xml_to_json")

    fname = filetools.join(config.get_data_path(), library.TVSHOW_FILE_OLD)
    if filetools.exists(fname):
        platformtools.dialog_ok("Biblioteca: Se va a actualizar al nuevo formato",
                                "Seleccione el nombre correcto de cada serie, si no está seguro pulse 'Cancelar'.",
                                "Hay nuevas opciones en 'Biblioteca' y en la 'configuración' del addon.")

        filetools.rename(library.TVSHOWS_PATH,  "SERIES_OLD")

        if not filetools.exists(library.TVSHOWS_PATH):
            filetools.mkdir(library.TVSHOWS_PATH)

            if filetools.exists(library.TVSHOWS_PATH):
                try:
                    data = filetools.read(fname)
                    for line in data.splitlines():
                        aux = line.rstrip('\n').split(",")
                        tvshow = aux[0].strip()
                        url = aux[1].strip()
                        channel = aux[2].strip()

                        serie = Item(contentSerieName=tvshow, url=url, channel=channel, action="episodios",
                                     title=tvshow)

                        patron = "^(.+)[\s]\((\d{4})\)$"
                        matches = re.compile(patron, re.DOTALL).findall(serie.contentSerieName)

                        if matches:
                            serie.infoLabels['title'] = matches[0][0]
                            serie.infoLabels['year'] = matches[0][1]
                        else:
                            serie.infoLabels['title'] = tvshow

                        library.save_library_tvshow(serie, list())

                    filetools.rename(fname, "series.xml.old")
                except EnvironmentError:
                    logger.info("ERROR al leer el archivo: {0}".format(fname))

            else:
                logger.info("ERROR, no se ha podido crear la nueva carpeta de SERIES")
        else:
            logger.info("ERROR, no se ha podido renombrar la antigua carpeta de SERIES")


def main():
    logger.info("pelisalacarta.library_service Actualizando series...")
    p_dialog = None

    try:

        if config.get_setting("updatelibrary") == "true":
            heading = 'Actualizando biblioteca....'
            p_dialog = platformtools.dialog_progress_bg('pelisalacarta', heading)
            p_dialog.update(0, '')
            show_list = []
            path = ""

            for path, folders, files in filetools.walk(library.TVSHOWS_PATH):
                show_list.extend([filetools.join(path, f) for f in files if f == "tvshow.json"])

            # fix float porque la division se hace mal en python 2.x
            t = float(100) / len(show_list)

            for i, tvshow_file in enumerate(show_list):

                serie = Item().fromjson(filetools.read(tvshow_file))

                logger.info("pelisalacarta.library_service serie="+serie.contentSerieName)
                logger.info("pelisalacarta.library_service Actualizando "+path)
                logger.info("pelisalacarta.library_service url " + serie.url)
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
                            library.save_library_episodes(serie, itemlist, serie, True)
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

    create_tvshows_from_xml()
    create_tvshows_from_json()
    main()
