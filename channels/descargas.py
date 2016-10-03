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
# Gestor de descargas
# ------------------------------------------------------------
import os
import re
import time

import channelselector
from core import config
from core import downloadtools
from core import filetools
from core import logger
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import platformtools


def mainlist(item):
    logger.info("pelisalacarta.core.descargas mainlist")
    itemlist = []

    status_color = {0: "orange", 1: "orange", 2: "green", 3: "red"}

    item.url = config.get_setting("downloadlistpath")

    for _file in sorted(filetools.listdir(item.url)):

        # Saltamos los archivos que no sean .json
        if not _file.endswith(".json"):
            continue

        filepath = filetools.join(item.url, _file)

        # Creamos el Item
        json_item = Item().fromjson(filetools.read(filepath))
        json_item.path = filepath
        json_item.thumbnail = json_item.contentThumbnail

        # Series
        if json_item.contentSerieName:
            json_item.title = "[COLOR %s][%i%%][/COLOR] [COLOR blue][%s][/COLOR] - %s" % \
                              (status_color[json_item.downloadStatus], json_item.downloadProgress,
                               json_item.contentSerieName, json_item.contentTitle)

        # Peliculas
        else:
            json_item.title = "[COLOR %s][%i%%][/COLOR] %s" % \
                              (status_color[json_item.downloadStatus], json_item.downloadProgress,
                               json_item.contentTitle)

        # Añadimos el item
        itemlist.append(json_item)

    estados = [item.downloadStatus for item in itemlist]

    # Si hay alguno completado
    if 2 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="clean_ready", title="Eliminar descargas completadas",
                                url=config.get_setting("downloadlistpath")))

    # Si hay alguno con error
    if 3 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="restart_error", title="Reiniciar descargas con error",
                                url=config.get_setting("downloadlistpath")))

    # Si hay alguno pendiente
    if 1 in estados or 0 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="downloadall", title="Descargar todo",
                                thumbnail=channelselector.get_thumbnail_path() + "Crystal_Clear_action_db_update.png",
                                url=config.get_setting("downloadlistpath")))

    if len(itemlist):
        itemlist.insert(0, Item(channel=item.channel, action="clean_all", title="Vaciar lista",
                                url=config.get_setting("downloadlistpath")))

    return itemlist


def update_library(item):
    video_path = filetools.join(config.get_library_path(), item.downloadFilename)

    # Peliculas
    if not item.contentSerieName:
        peli = Item(infoLabels=item.infoLabels, fanart=item.fanart, thumbnail=item.thumbnail)
        open(os.path.splitext(video_path)[0] + ".nfo", "wb").write(
            "https://www.themoviedb.org/movie/%s" % peli.infoLabels["tmdb_id"])
        open(os.path.splitext(video_path)[0] + ".json", "wb").write(peli.tojson())

    # Series
    else:
        serie = Item()
        if item.infoLabels.get("tmdb_id"):
            serie.infoLabels = {"tmdb_id": item.infoLabels.get("tmdb_id")}
            serie.contentSerieName = item.contentSerieName
            tmdb.find_and_set_infoLabels_tmdb(serie)

        open(filetools.join(filetools.dirname(video_path), "tvshow.json"), "wb").write(serie.tojson())

        if item.infoLabels.get("tmdb_id"):
            serie.contentSeason = item.contentSeason
            serie.contentEpisodeNumber = item.contentEpisodeNumber
            logger.info(item.tostring("\n"))
            tmdb.find_and_set_infoLabels_tmdb(serie)

        open(os.filetools.join(filetools.dirname(video_path), "tvshow.nfo"), "wb").write(
            "https://www.themoviedb.org/tv/%s" % serie.infoLabels.get("tmdb_id"))
        open(os.path.splitext(video_path)[0] + ".json", "wb").write(serie.tojson())


def clean_all(item):
    """
    Elimina todas las descargas de la lista
    @type item: item
    @param item: elemento que contiene las descargas
    """
    logger.info("pelisalacarta.core.descargas clean_all")
    for fichero in sorted(filetools.listdir(item.url)):
        filetools.remove(filetools.join(item.url, fichero))

    platformtools.itemlist_refresh()


def clean_ready(item):
    """
    Elimina todas las descargas completadas de la lista
    @type item: item
    @param item: elemento que contiene las descargas
    """
    logger.info("pelisalacarta.core.descargas clean_ready")
    for fichero in sorted(filetools.listdir(item.url)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(filetools.join(item.url, fichero)))
            if download_item.downloadStatus == 2:
                filetools.remove(filetools.join(item.url, fichero))

    platformtools.itemlist_refresh()


def restart_error(item):
    """
    Restablece todas las descargas marcadas como error
    @type item: item
    @param item: elemento que contiene las descargas
    """
    logger.info("pelisalacarta.core.descargas restart_error")
    for fichero in sorted(filetools.listdir(item.url)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(filetools.join(item.url, fichero)))
            if download_item.downloadStatus == 3:
                if filetools.isfile(filetools.join(config.get_library_path(), download_item.downloadFilename)):
                    filetools.remove(filetools.join(config.get_library_path(), download_item.downloadFilename))
                download_item.downloadStatus = 0
                download_item.downloadComplete = 0
                download_item.downloadProgress = 0
                filetools.write(filetools.join(item.url, fichero), download_item.tojson())

    platformtools.itemlist_refresh()


def menu(item):
    """
    Muestra el menu con las opciones disponibles para cada descarga
    @type item: item
    @param item: elemento que contiene las descargas
    """
    logger.info("pelisalacarta.core.descargas menu")

    # Opciones disponibles para el menu
    op = ["Descargar", "Eliminar de la lista", "Reiniciar descarga"]

    opciones = []

    # Opciones para el menu
    if item.downloadStatus == 0:  # Sin descargar
        opciones.append(op[0])  # Iniciar descarga
        opciones.append(op[1])  # Eliminar de la lista

    if item.downloadStatus == 1:  # descarga parcial
        opciones.append(op[0])  # Continuar descarga
        opciones.append(op[2])  # Reiniciar descarga
        opciones.append(op[1])  # Eliminar de la lista

    if item.downloadStatus == 2:  # descarga completada
        opciones.append(op[1])  # Eliminar de la lista
        opciones.append(op[2])  # Reiniciar descarga

    if item.downloadStatus == 3:  # descarga con error
        opciones.append(op[2])  # Reiniciar descarga
        opciones.append(op[1])  # Eliminar de la lista

    # Mostramos el dialogo
    seleccion = platformtools.dialog_select("Elige una opción", opciones)

    # -1 es cancelar
    if seleccion == -1:
        return

    logger.info("pelisalacarta.core.descargas menu opcion=%s" % (opciones[seleccion]))
    # Opcion Eliminar
    if opciones[seleccion] == op[1]:
        filetools.remove(item.path)

    # Opcion inicaiar descarga
    if opciones[seleccion] == op[0]:
        start_download(item, True)

    # Reiniciar descarga
    if opciones[seleccion] == op[2]:
        if filetools.isfile(filetools.join(config.get_library_path(), item.downloadFilename)):
            filetools.remove(filetools.join(config.get_library_path(), item.downloadFilename))
        json_item = Item().fromjson(filetools.read(item.path))
        json_item.downloadStatus = 0
        json_item.downloadComplete = 0
        json_item.downloadProgress = 0
        filetools.write(item.path, json_item.tojson())

    platformtools.itemlist_refresh()


def download_from_url(url, item, continuar=True):
    """
    Inicia la descarga una vez ya tenemos la url del vídeo
    @type url: str
    @param url: url de la descarga
    @type item: item
    @param item: elemento que contiene las descargas
    @type continuar: bool
    @param continuar: establece si resume la descarga
    """
    logger.info("pelisalacarta.core.descargas download_url - Intentando descargar: %s" % url)
    logger.debug("item:\n" + item.tostring('\n'))
    # Obtenemos la ruta de descarga y el nombre del archivo

    download_path = filetools.dirname(filetools.join(config.get_library_path(), item.downloadFilename))
    file_name = os.path.basename(filetools.join(config.get_library_path(), item.downloadFilename))

    # Creamos la carpeta si no existe
    if not filetools.exists(download_path):
        filetools.mkdir(download_path)

    update_library(item)

    # Mostramos el progreso
    progreso = platformtools.dialog_progress("Descargas", "Iniciando descarga...")

    # Lanzamos la descarga
    d = downloadtools.Downloader(url, download_path, file_name, resume=continuar).start()

    # Monitorizamos la descarga hasta que se termine o se cancele
    while d.status.state == d.states.downloading and not progreso.iscanceled():
        time.sleep(0.1)
        line1 = "%s" % d.status.filename
        line2 = "%.2f%% - %.2f %s de %.2f %s a %.2f %s/s (%d/%d)" % \
                (d.status.progress, d.status.downloaded, d.status.downloaded_unit, d.status.size, d.status.size_unit,
                 d.status.speed, d.status.speed_unit, d.status.downloading, d.status.parts)
        line3 = "Tiempo restante: %s" % d.status.time
        progreso.update(int(d.status.progress), line1, line2, line3)

    # Obtenemos el estado:
    status = 0
    # Si se ha producido un error
    if d.status.state == d.states.error:
        logger.info("pelisalacarta.core.descargas download_video - Error al intentar descargar %s" % url)
        d.stop()
        progreso.close()
        status = 3

    # Si aun está descargando es que se ha cancelado, detenemos
    elif d.status.state == d.states.downloading:
        logger.info("pelisalacarta.core.descargas download_video - Descarga detenida")
        d.stop()
        progreso.close()
        status = 1

    # Si se ha terminado
    elif d.status.state == d.states.finish:
        logger.info("pelisalacarta.core.descargas download_video - Descargado correctamente")
        progreso.close()
        status = 2

    '''
    Devolvemos el resumen de la descarga:
      -Estado
      -Tamaño
      -Descargado
      -Nombre del archivo
    '''
    _dir = os.path.dirname(item.downloadFilename)
    _file = filetools.join(_dir, d.status.filename)

    return {"downloadStatus": status, "downloadSize": d.status.size_bytes, "downloadProgress": d.status.progress,
            "downloadCompleted": d.status.downloaded_bytes, "downloadFilename": _file}


def download_from_server(item, continuar=False):
    """
    Obtiene las urls disponibles para un server, y va probando hasta encontrar una que funcione
    @type item: item
    @param item: elemento que contiene las descargas
    @type continuar: bool
    @param continuar: establece si resume la descarga
    """
    logger.info("pelisalacarta.core.descargas download_from_server")

    video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(item.server, item.url, item.password, True)

    # Si no esta disponible, salimos
    if not puedes:
        logger.info("pelisalacarta.core.descargas get_video_urls_from_item: EL VIDEO NO ESTA DISPONIBLE")
        update_json(item.path, {"status": 3})
        return 3

    else:
        logger.info("pelisalacarta.core.descargas download_video - EL VIDEO SI ESTA DISPONIBLE")

        result = {"downloadStatus": 3}

        # Recorre todas las opciones hasta que consiga descargar una correctamente
        for video_url in reversed(video_urls):

            result = download_from_url(video_url[1], item, continuar)

            # Descarga cancelada, no probamos mas
            if result["downloadStatus"] == 1:
                break
            # Descarga completada, no probamos mas
            if result["downloadStatus"] == 2:
                break

            # Error en la descarga, continuamos con la siguiente opcion
            if result["downloadStatus"] == 3:
                continue

        # Actualizamos el json, con la info de la descarga
        update_json(item.path, result)

        # Devolvemos el estado
        return result["downloadStatus"]


def update_json(path, params):
    """
    Añade al JSON los parametros pasados por el argumento params
    @type path: str
    @param path: ruta
    @type params: list
    @param params: argumentos a pasar
    """
    item = Item().fromjson(filetools.read(path))
    item.__dict__.update(params)
    filetools.write(path, item.tojson())


def downloadall(item):
    """
    Descarga toda la lista de descargas
    @type item: item
    @param item: contiene las descargas
    """
    time.sleep(0.5)
    for fichero in sorted(filetools.listdir(item.url)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(filetools.join(item.url, fichero)))
            download_item.path = filetools.join(item.url, fichero)
            if download_item.downloadStatus in [0, 1]:

                res = start_download(download_item, True)
                platformtools.itemlist_refresh()
                # Si se ha cancelado paramos
                if res == 1:
                    break


def ordenar(item):
    import re
    # List con el orden de calidades (de mejor a peor)

    full_hd_names = ["FULLHD", "1080P"]
    hd_names = ["HD", "HD 720", "MICROHD", "720P", "HDTV"]
    sd_names = ["SD", "480p", "360p", "240p"]
    calidades = full_hd_names + hd_names + sd_names

    if not item.quality:
        re_calidades = "|".join(calidades).replace("-", "\-")
        calidad = re.compile(".*?([" + re_calidades + "]+).*?", re.IGNORECASE).findall(item.title)
        if calidad:
            item.quality = calidad[-1]

    return calidades.index(item.calidad) if item.quality in calidades else len(calidades)


def download_from_best_server(item):
    """
    Obtiene los servers disponibles para un video, los ordena por calidad y va probando hasta encontrar uno que funcione
    @type item: item
    @param item: contiene la descarga
    """
    logger.info("pelisalacarta.core.descargas download_from_best_server")

    # importamos el canal
    channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])

    # Obtenemos el listado de servers
    play_items = getattr(channel, item.contentAction)(item)

    # Las ordenamos segun calidad
    play_items.sort(key=ordenar)

    result = 3
    # Recorremos el listado de servers, hasta encontrar uno que funcione
    for play_item in play_items:

        # Si el canal tiene funcion play, la lanza
        if hasattr(channel, "play"):
            itemlist = getattr(channel, "play")(play_item)
            if len(itemlist):
                play_item = itemlist[0]
            else:
                continue

        # Lanzamos la descarga
        download_item = item.clone()
        download_item.__dict__.update(play_item.__dict__)

        result = download_from_server(download_item, True)

        # Tanto si se cancela la descarga como si se completa dejamos de probar mas opciones
        if result in [1, 2]:
            break
    return result


def start_download(item, continuar=False):
    """
    Inicia la descarga de un item de la lista de descargas
    @type item: item
    @param item: contiene la descarga
    @type continuar: bool
    @param continuar: establece si resume la descarga
    """
    logger.info("pelisalacarta.core.descargas start_download")

    # Ya tenemnos server, solo falta descargar
    if item.contentAction == "play":
        return download_from_server(item, continuar)

    # No tenemos server, necesitamos buscar el mejor
    else:
        return download_from_best_server(item)


def get_episodes(item):
    """
    Función para obtener todos los episodios de una serie
      Usa el contenido del titulo para generar el nombre del archivo
      Elimina items como "Añadir serie a la biblioteca", etc...
    @type item: item
    @param item: contiene los episodios
    """
    remove_items = ["add_serie_to_library", "download_all_episodes"]

    logger.info("pelisalacarta.core.descargas get_episodes")

    # importamos el canal
    channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])

    # Obtenemos el listado de episodios
    episodios = getattr(channel, item.contentAction)(item)
    episodios = [episodio for episodio in episodios if episodio.action not in remove_items]

    for x in range(len(episodios)):
        episodios[x].contentSerieName = item.contentSerieName
        episodios[x].infoLabels = item.infoLabels
        episodios[x].contentAction = episodios[x].action
        episodios[x].contentChannel = episodios[x].channel

        episodios[x].action = "menu"
        episodios[x].channel = "descargas"
        episodios[x].folder = True
        episodios[x].downloadStatus = 0
        episodios[x].downloadProgress = 0
        episodios[x].downloadSize = 0
        episodios[x].downloadCompleted = 0
        episodios[x].contentSeason, episodios[x].contentEpisodeNumber = scrapertools.get_season_and_episode(
            episodios[x].title.lower()).split("x")

        if not episodios[x].contentSeason or not episodios[x].contentEpisodeNumber or not episodios[x].contentTitle:
            episodios[x].downloadFilename = filetools.join(item.downloadFilename,
                                                         downloadtools.limpia_nombre_excepto_1(episodios[x].title))
        else:
            episodios[x].downloadFilename = filetools.join(item.downloadFilename,
                                                         "{0}x{1} - {2}".format(episodios[x].contentSeason,
                                                                                episodios[x].contentEpisodeNumber,
                                                                                episodios[x].contentTitle))

    return episodios


def save_download_movie(item):
    logger.info("pelisalacarta.core.descargas save_download_movie")
    item.contentAction = item.from_action if item.from_action else item.action
    if item.contentChannel == "list":
        item.contentChannel = item.from_channel if item.from_channel else item.channel

    titulo = item.contentTitle
    if not titulo:
        titulo = re.sub("\[[^\]]+\]", "", item.fulltitle)
        titulo = re.sub("\([^\)]+\)", "", titulo).strip()
    if not titulo:
        titulo = re.sub("\[[^\]]+\]", "", item.title)
        titulo = re.sub("\([^\)]+\)", "", titulo).strip()

    item.contentTitle = titulo
    item.show = ""

    tmdb.find_and_set_infoLabels_tmdb(item)

    item.action = "menu"
    item.channel = "descargas"
    item.folder = True
    item.downloadStatus = 0
    item.downloadProgress = 0
    item.downloadSize = 0
    item.downloadCompleted = 0
    item.downloadFilename = filetools.join("Descargas", "Cine", downloadtools.limpia_nombre_excepto_1(item.contentTitle))
    item.downloadFilename += " [" + item.contentChannel + "]"

    item.path = filetools.join(config.get_setting("downloadlistpath"), str(time.time()) + ".json")
    filetools.write(item.path, item.tojson())
    start = platformtools.dialog_yesno(config.get_localized_string(30101), "¿Iniciar la descarga ahora?")

    if not start:
        platformtools.dialog_ok(config.get_localized_string(30101), item.contentTitle,
                                config.get_localized_string(30109))
    else:
        start_download(item)


def save_download_tvshow(item):
    item.contentAction = item.from_action if item.from_action else item.action
    item.contentChannel = item.from_channel if item.from_channel else item.channel

    titulo = item.contentSerieName
    if not titulo:
        titulo = item.show
    item.contentSerieName = titulo

    tmdb.find_and_set_infoLabels_tmdb(item)

    item.downloadFilename = filetools.join("Descargas", "Series", item.contentSerieName)
    itemlist = get_episodes(item)

    progreso = platformtools.dialog_progress("Descargas", "Añadiendo capitulos...")

    for x in range(len(itemlist)):
        progreso.update(x * 100 / len(itemlist), os.path.basename(itemlist[x].downloadFilename))
        itemlist[x].path = filetools.join(config.get_setting("downloadlistpath"), str(time.time()) + ".json")
        filetools.write(itemlist[x].path, itemlist[x].tojson())
        time.sleep(0.1)

    progreso.close()

    start = platformtools.dialog_yesno(config.get_localized_string(30101), "¿Iniciar la descarga ahora?")

    if not start:
        platformtools.dialog_ok(config.get_localized_string(30101),
                                str(len(itemlist)) + " capitulos de: " + item.contentSerieName,
                                config.get_localized_string(30109))
    else:
        for x in range(len(itemlist)):
            res = start_download(itemlist[x])
            if res == 1:
                break


# Para actualizar las descargas a .json
def check_bookmark(savepath):
    from channels import favoritos
    for fichero in filetools.listdir(savepath):
        # Ficheros antiguos (".txt")
        if fichero.endswith(".txt"):
            # Esperamos 0.1 segundos entre ficheros, para que no se solapen los nombres de archivo
            time.sleep(0.1)

            # Obtenemos el item desde el .txt
            canal, titulo, thumbnail, plot, server, url, fulltitle = favoritos.readbookmark(fichero, savepath)
            item = Item(channel=canal, action="play", url=url, server=server, title=fulltitle, thumbnail=thumbnail,
                        plot=plot, fanart=thumbnail, extra=filetools.join(savepath, fichero), fulltitle=fulltitle,
                        folder=False)

            # Eliminamos el .txt
            os.remove(item.extra)
            item.extra = ""

            # Guardamos el archivo
            filename = filetools.join(savepath, str(time.time()) + ".json")
            filetools.write(filename, item.tojson())


check_bookmark(config.get_setting("downloadlistpath"))
