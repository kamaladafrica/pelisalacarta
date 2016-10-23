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


def convert_old_to_v4():
    logger.info("pelisalacarta.platformcode.library_service convert_old_to_v4")
    path_series_xml = filetools.join(config.get_data_path(), "series.xml")
    path_series_json = filetools.join(config.get_data_path(), "series.json")
    series_insertadas = 0
    series_fallidas = 0
    version = 'v?'

    # Renombrar carpeta Series y crear una vacia
    import time
    new_name = "SERIES_OLD_" + str(time.time())
    path_series_old = filetools.join(library.LIBRARY_PATH, new_name)
    if filetools.rename(library.TVSHOWS_PATH,  new_name):
        if not filetools.mkdir(library.TVSHOWS_PATH):
            logger.info("ERROR, no se ha podido crear la nueva carpeta de SERIES")
            return False
    else:
        logger.error("ERROR, no se ha podido renombrar la antigua carpeta de SERIES")
        return False

    # Convertir libreria de v1(xml) a v4
    if filetools.exists(path_series_xml):
        try:
            data = filetools.read(path_series_xml)
            for line in data.splitlines():
                try:
                    aux = line.rstrip('\n').split(",")
                    tvshow = aux[0].strip()
                    url = aux[1].strip()
                    channel = aux[2].strip()

                    serie = Item(contentSerieName=tvshow, url=url, channel=channel, action="episodios",
                                 title=tvshow, active=True)

                    patron = "^(.+)[\s]\((\d{4})\)$"
                    matches = re.compile(patron, re.DOTALL).findall(serie.contentSerieName)

                    if matches:
                        serie.infoLabels['title'] = matches[0][0]
                        serie.infoLabels['year'] = matches[0][1]
                    else:
                        serie.infoLabels['title'] = tvshow

                    insertados, sobreescritos, fallidos = library.save_library_tvshow(serie, list())
                    if fallidos == 0:
                        series_insertadas += 1
                        platformtools.dialog_notification("Serie actualizada", serie.infoLabels['title'])
                    else:
                        series_fallidas += 1
                except:
                    series_fallidas += 1

            filetools.rename(path_series_xml, "series.xml.old")
            version = 'v4'

        except EnvironmentError:
            logger.info("ERROR al leer el archivo: %s" % path_series_xml)
            return False

    # Convertir libreria de v2(json) a v4
    if filetools.exists(path_series_json):
        try:
            data = jsontools.load_json(filetools.read(path_series_json))
            for tvshow in data:
                for channel in data[tvshow]["channels"]:
                    try:
                        serie = Item(contentSerieName=data[tvshow]["channels"][channel]["tvshow"],
                                     url=data[tvshow]["channels"][channel]["url"], channel=channel, action="episodios",
                                     title=data[tvshow]["name"], active=True)
                        if not tvshow.startswith("t_"):
                            serie.infoLabels["tmdb_id"] = tvshow

                        insertados, sobreescritos, fallidos = library.save_library_tvshow(serie, list())
                        if fallidos == 0:
                            series_insertadas += 1
                            platformtools.dialog_notification("Serie actualizada", serie.infoLabels['title'])
                        else:
                            series_fallidas += 1
                    except:
                        series_fallidas += 1

            filetools.rename(path_series_json, "series.json.old")
            version = 'v4'

        except EnvironmentError:
            logger.info("ERROR al leer el archivo: %s" % path_series_json)
            return False

    # Convertir libreria de v3 a v4
    if version != 'v4':
        # Obtenemos todos los tvshow.json de la biblioteca de SERIES_OLD recursivamente
        for raiz, subcarpetas, ficheros in filetools.walk(path_series_old):
            for f in ficheros:
                if f == "tvshow.json":
                    try:
                        serie = Item().fromjson(filetools.read(filetools.join(raiz, f)))
                        insertados, sobreescritos, fallidos = library.save_library_tvshow(serie, list())
                        if fallidos == 0:
                            series_insertadas += 1
                            platformtools.dialog_notification("Serie actualizada", serie.infoLabels['title'])
                        else:
                            series_fallidas += 1
                    except:
                        series_fallidas += 1

    config.set_setting("library_version", 'v4')

    platformtools.dialog_notification("Biblioteca actualizada al nuevo formato",
                                      "%s series convertidas y %s series descartadas. A continuación se va a "
                                      "obtener la información de todos los episodios" %
                                      (series_insertadas, series_fallidas), time=12000)

    # Por ultimo limpia la libreria, por que las rutas anteriores ya no existen
    library.clean()

    return True


def main(overwrite=True):
    logger.info("pelisalacarta.library_service Actualizando series...")
    p_dialog = None

    try:

        if config.get_setting("updatelibrary") == "true":
            updatelibrary_wait = [0, 10000, 20000, 30000, 60000]
            wait = updatelibrary_wait[int(config.get_setting("updatelibrary_wait"))]
            if wait > 0:
                import xbmc
                xbmc.sleep(wait)

            heading = 'Actualizando biblioteca....'
            p_dialog = platformtools.dialog_progress_bg('pelisalacarta', heading)
            p_dialog.update(0, '')
            show_list = []

            for path, folders, files in filetools.walk(library.TVSHOWS_PATH):
                show_list.extend([filetools.join(path, f) for f in files if f == "tvshow.nfo"])

            # fix float porque la division se hace mal en python 2.x
            t = float(100) / len(show_list)

            for i, tvshow_file in enumerate(show_list):
                serie = Item().fromjson(filetools.read(tvshow_file, 1))
                path = filetools.dirname(tvshow_file)

                if serie.contentSeriename == "":
                    serie.contentSeriename = serie.show
                logger.info("pelisalacarta.library_service serie=" + serie.contentSerieName)
                p_dialog.update(int(math.ceil((i+1) * t)), heading, serie.contentSeriename)

                if not serie.active:
                    continue

                # si la serie esta activa se actualiza
                logger.info("pelisalacarta.library_service Actualizando " + path)

                # logger.debug("%s: %s" %(serie.contentSerieName,str(list_canales) ))
                for channel, url in serie.library_urls.items():
                    serie.channel = channel
                    serie.url = url
                    p_dialog.update(int(math.ceil((i + 1) * t)), heading, "%s: %s" % (serie.contentSerieName,
                                                                                      serie.channel.capitalize()))
                    try:
                        pathchannels = filetools.join(config.get_runtime_path(), "channels", serie.channel + '.py')
                        logger.info("pelisalacarta.library_service Cargando canal: " + pathchannels + " " +
                                    serie.channel)

                        obj = imp.load_source(serie.channel, pathchannels)
                        itemlist = obj.episodios(serie)

                        try:
                            library.save_library_episodes(path, itemlist, serie, silent=True, overwrite=overwrite)

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
    if config.get_setting("library_version") != 'v4':
        platformtools.dialog_ok(config.PLUGIN_NAME.capitalize(), "Se va a actualizar la biblioteca al nuevo formato",
                                "Seleccione el nombre correcto de cada serie, si no está seguro pulse 'Cancelar'.")

        if not convert_old_to_v4():
            platformtools.dialog_ok(config.PLUGIN_NAME.capitalize(),
                                    "ERROR, al actualizar la biblioteca al nuevo formato")
        else:
            main(overwrite=False)
    else:
        main(overwrite=False)
