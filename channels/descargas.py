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
import sys
import re
from core import config
from core.downloader import Downloader
from core import scrapertools
from core import logger
from core import servertools
from core import filetools
from platformcode import platformtools
from core.item import Item
import time
from core import tmdb


def mainlist(item):
    logger.info("pelisalacarta.channels.descargas mainlist")
    
    itemlist = []
    status_color = {0: "orange", 1: "orange", 2: "green", 3: "red"}
    item.url = config.get_setting("downloadlistpath")
    
    series = {}

    for file in sorted(filetools.listdir(item.url)):
        file = os.path.join(item.url, file)

        # Saltamos los archivos que no sean .json
        if not file.endswith(".json"): continue

        i = Item().fromjson(filetools.read(file))
        i.path = file
        i.thumbnail = i.contentThumbnail
        
        #item.serie_name significa que estamos desntro de una serie
        if not item.serie_name:
          # Series
          if i.contentType == "episode":
              serie_name = "%s [%s]" % (i.contentSerieName, i.contentChannel)
              if not serie_name in series:
                title = serie_name
                series = {serie_name: {"downloadProgress": [i.downloadProgress], "downloadStatus": [i.downloadStatus]}}
                i.title=title
                i.contentSeason = ""
                i.contntEpisodeNumber = ""
                i.action = "mainlist"
                i.serie_name = serie_name
                itemlist.append(i)
              else:
                series[serie_name]["downloadProgress"].append(i.downloadProgress)
                series[serie_name]["downloadStatus"].append(i.downloadStatus)


          # Peliculas
          elif i.contentType == "movie":
              i.title = "[COLOR %s][%i%%][/COLOR] %s" % (status_color[i.downloadStatus], i.downloadProgress, i.contentTitle)
              itemlist.append(i)
        else:
            if i.contentType == "episode":
              serie_name = "%s [%s]" % (i.contentSerieName, i.contentChannel)
              if serie_name == item.serie_name:
                i.title = "[COLOR %s][%i%%][/COLOR] %s" % (status_color[i.downloadStatus], i.downloadProgress, i.contentTitle)
                itemlist.append(i)  
    
    for i in itemlist:
      if i.title in series:
        if any(series[i.title]["downloadStatus"]) == 3:
          downloadStatus = 3
        elif all(series[i.title]["downloadStatus"]) == 2:
          downloadStatus = 2
        else:
          downloadStatus = 1
          
        downloadProgress = sum(series[i.title]["downloadProgress"]) / len(series[i.title]["downloadProgress"])
        
        i.title = "[COLOR %s][%i%%][/COLOR] %s [%s]" % (status_color[downloadStatus], downloadProgress, i.contentSerieName, i.contentChannel)
        i.downloadStatus = downloadStatus
                    
    estados = [i.downloadStatus for i in itemlist]
    

    # Si hay alguno completado
    if 2 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="clean_ready", title="Eliminar descargas completadas",
                                url=config.get_setting("downloadlistpath"), serie_name = item.serie_name))

    # Si hay alguno con error
    if 3 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="restart_error", title="Reiniciar descargas con error",
                                url=config.get_setting("downloadlistpath"), serie_name = item.serie_name))

    # Si hay alguno pendiente
    if 1 in estados or 0 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="download_all", title="Descargar todo",
                                url=config.get_setting("downloadlistpath"), serie_name = item.serie_name))

    if len(itemlist):
        itemlist.insert(0, Item(channel=item.channel, action="clean_all", title="Eliminar todo",
                                url=config.get_setting("downloadlistpath"), serie_name = item.serie_name))

    return itemlist


def clean_all(item):
    logger.info("pelisalacarta.channels.descargas clean_all")
    
    
    for fichero in sorted(filetools.listdir(item.url)):
        download_item = Item().fromjson(filetools.read(os.path.join(item.url, fichero)))
        serie_name = "%s [%s]" % (download_item.contentSerieName, download_item.contentChannel)
        if not item.serie_name or item.serie_name == serie_name:
          if fichero.endswith(".json"):
              filetools.remove(os.path.join(item.url, fichero))

    platformtools.itemlist_refresh()


def clean_ready(item):
    logger.info("pelisalacarta.channels.descargas clean_ready")
    for fichero in sorted(filetools.listdir(item.url)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(item.url, fichero)))
            serie_name = "%s [%s]" % (download_item.contentSerieName, download_item.contentChannel)
            if not item.serie_name or item.serie_name == serie_name:
              if download_item.downloadStatus == 2:
                  filetools.remove(os.path.join(item.url, fichero))

    platformtools.itemlist_refresh()


def restart_error(item):
    logger.info("pelisalacarta.channels.descargas restart_error")
    for fichero in sorted(filetools.listdir(item.url)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(item.url, fichero)))
            serie_name = "%s [%s]" % (download_item.contentSerieName, download_item.contentChannel)
            if not item.serie_name or item.serie_name == serie_name:
              if download_item.downloadStatus == 3:
                  if filetools.isfile(os.path.join(config.get_setting("downloadpath"), download_item.downloadFilename)):
                      filetools.remove(os.path.join(config.get_setting("downloadpath"), download_item.downloadFilename))
                  download_item.downloadStatus = 0
                  download_item.downloadComplete = 0
                  download_item.downloadProgress = 0
                  download_item.downloadUrl = ""
                  filetools.write(os.path.join(item.url, fichero), download_item.tojson())

    platformtools.itemlist_refresh()


def download_all(item):
    time.sleep(0.5)
    for fichero in sorted(filetools.listdir(item.url)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(item.url, fichero)))
            serie_name = "%s [%s]" % (download_item.contentSerieName, download_item.contentChannel)
            if not item.serie_name or item.serie_name == serie_name:
              download_item.path = os.path.join(item.url, fichero)
              if download_item.downloadStatus in [0, 1]:

                  res = start_download(download_item)
                  platformtools.itemlist_refresh()
                  # Si se ha cancelado paramos
                  if res == 1: break


def menu(item):
    logger.info("pelisalacarta.channels.descargas menu")

    # Opciones disponibles para el menu
    op = ["Descargar", "Eliminar de la lista", "Reiniciar descarga"]

    opciones = []

    # Opciones para el menu
    if item.downloadStatus == 0:  # Sin descargar
        opciones.append(op[0])  # Descargar
        opciones.append(op[1])  # Eliminar de la lista

    if item.downloadStatus == 1:  # descarga parcial
        opciones.append(op[0])  # Descargar
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
    if seleccion == -1: return

    logger.info("pelisalacarta.channels.descargas menu opcion=%s" % (opciones[seleccion]))
    # Opcion Eliminar
    if opciones[seleccion] == op[1]:
        filetools.remove(item.path)

    # Opcion inicaiar descarga
    if opciones[seleccion] == op[0]:
        start_download(item)

    # Reiniciar descarga
    if opciones[seleccion] == op[2]:
        if filetools.isfile(os.path.join(config.get_setting("downloadpath"), item.downloadFilename)):
            filetools.remove(os.path.join(config.get_setting("downloadpath"), item.downloadFilename))
        JSONItem = Item().fromjson(filetools.read(item.path))
        JSONItem.downloadStatus = 0
        JSONItem.downloadComplete = 0
        JSONItem.downloadProgress = 0
        JSONItem.downloadUrl = ""
        filetools.write(item.path, JSONItem.tojson())

    platformtools.itemlist_refresh()


def move_to_libray(item):
    # Copiamos el archivo a la biblioteca
    filetools.copy(filetools.join(config.get_setting("downloadpath"), item.downloadFilename),
                   filetools.join(config.get_library_path(), filetools.basename(item.downloadFilename)))

    # Eliminamos el origen
    filetools.remove(filetools.join(config.get_setting("downloadpath"), item.downloadFilename))

    # Añadimos el contenido a la biblioteca
    # TODO: incorporar funcion
    # lirbary.add_download_to_library(item, filename)


def download_from_url(url, item):
    logger.info("pelisalacarta.channels.descargas download_from_url - Intentando descargar: %s" % (url))

    # Obtenemos la ruta de descarga y el nombre del archivo
    download_path = os.path.dirname(filetools.join(config.get_setting("downloadpath"), item.downloadFilename))
    file_name = os.path.basename(filetools.join(config.get_setting("downloadpath"), item.downloadFilename))

    # Creamos la carpeta si no existe
    if not filetools.exists(download_path):
        filetools.mkdir(download_path)

    # Mostramos el progreso
    progreso = platformtools.dialog_progress("Descargas", "Iniciando descarga...")

    # Lanzamos la descarga
    d = Downloader(url, filetools.encode(download_path), filetools.encode(file_name))
    d.start()

    # Monitorizamos la descarga hasta que se termine o se cancele
    while d.state == d.states.downloading and not progreso.iscanceled():
        time.sleep(0.1)
        line1 = "%s" % (filetools.decode(d.filename))
        line2 = "%.2f%% - %.2f %s de %.2f %s a %.2f %s/s (%d/%d)" % (
        d.progress, d.downloaded[1], d.downloaded[2], d.size[1], d.size[2], d.speed[1], d.speed[2], d.connections[0],
        d.connections[1])
        line3 = "Tiempo restante: %s" % (d.remaining_time)
        progreso.update(int(d.progress), line1, line2, line3)

    # Descarga detenida. Obtenemos el estado:
    # Se ha producido un error en la descarga
    if d.state == d.states.error:
        logger.info("pelisalacarta.channels.descargas download_video - Error al intentar descargar %s" % (url))
        d.stop()
        progreso.close()
        status = 3

    # Aun está descargando (se ha hecho click en cancelar)
    elif d.state == d.states.downloading:
        logger.info("pelisalacarta.channels.descargas download_video - Descarga detenida")
        d.stop()
        progreso.close()
        status = 1

    # La descarga ha finalizado
    elif d.state == d.states.completed:
        logger.info("pelisalacarta.channels.descargas download_video - Descargado correctamente")
        progreso.close()
        status = 2

        if item.downloadSize and item.downloadSize != d.size[0]:
            status = 3

    
    
    dir = os.path.dirname(item.downloadFilename)
    file = filetools.join(dir, filetools.decode(d.filename))
    
    if status == 2:
        move_to_libray(item.clone(downloadFilename =  file))
        
    return {"downloadUrl": d.download_url, "downloadStatus": status, "downloadSize": d.size[0],
            "downloadProgress": d.progress, "downloadCompleted": d.downloaded[0], "downloadFilename": file}


def download_from_server(item):
    logger.info("pelisalacarta.channels.descargas download_from_server")

    if item.server == "torrent":  # De momento las descargas torrents no estan permitidas, ya que funcionan de forma diferente
        puedes = False

    else:
        video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(item.server, item.url, item.password,
                                                                                True)

        # Si no esta disponible, salimos
    if not puedes:
        logger.info("pelisalacarta.channels.descargas get_video_urls_from_item: EL VIDEO NO ESTA DISPONIBLE")
        return {"downloadStatus": 3}

    else:
        logger.info("pelisalacarta.channels.descargas download_video - EL VIDEO SI ESTA DISPONIBLE")

        result = {"downloadStatus": 3}

        # Recorre todas las opciones hasta que consiga descargar una correctamente
        for video_url in reversed(video_urls):

            result = download_from_url(video_url[1], item)

            # Descarga cancelada, no probamos mas
            if result["downloadStatus"] == 1:
                break

            # Descarga completada, no probamos mas
            if result["downloadStatus"] == 2:
                break

            # Error en la descarga, continuamos con la siguiente opcion
            if result["downloadStatus"] == 3:
                continue

        # Devolvemos el estado
        return result


def update_json(path, params):
    item = Item().fromjson(filetools.read(path))
    item.__dict__.update(params)
    filetools.write(path, item.tojson())



def ordenar(item):
    import re

    # TODO: completar lista
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

    if item.quality in calidades:
        return calidades.index(item.quality)
    else:
        return len(calidades)


def download_from_best_server(item):
    logger.info("pelisalacarta.channels.descargas download_from_best_server")

    progreso = platformtools.dialog_progress("Descargas", "Obteniendo lista de servidores disponibles...")

    # importamos el canal
    channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])

    if hasattr(channel, item.contentAction):
        # Obtenemos el listado de servers
        play_items = getattr(channel, item.contentAction)(item)
    else:
        play_items = servertools.find_video_items(item)
    
    progreso.update(100, "Servidores disponibles: %s" % len(play_items))

    # Las ordenamos segun calidad
    play_items.sort(key=ordenar)

    result =  {"downloadStatus": 3}
    if progreso.iscanceled():
        result["downloadStatus"] = 1
        return result
          
    time.sleep(3)
    progreso.close
    # Recorremos el listado de servers, hasta encontrar uno que funcione
    for play_item in play_items:

        if play_item.action == "play":
            # Si el canal tiene funcion play, la lanza
            if hasattr(channel, "play"):
                itemlist = getattr(channel, "play")(play_item)
                if len(itemlist):
                    play_item = itemlist[0]
                else:
                    logger.info("No hay nada que reproducir")
                    return result
        else:
            continue

        # Lanzamos la descarga
        download_item = item.clone()
        download_item.__dict__.update(play_item.__dict__)

        result = download_from_server(download_item)
        
        if progreso.iscanceled():
          result["downloadStatus"] = 1

        # Tanto si se cancela la descarga como si se completa dejamos de probar mas opciones
        if result["downloadStatus"] in [1, 2]:
            break
    return result


def start_download(item):
    logger.info("pelisalacarta.channels.descargas start_download")

    # Descarga pausada, intentamos continuar con la misma url
    if item.downloadUrl:
        ret = download_from_url(item.downloadUrl, item)
        if ret["downloadStatus"] != 3:
            update_json(item.path, ret)
            return ret["downloadStatus"]

    # Ya tenemnos server, solo falta descargar
    if item.contentAction == "play":
        ret = download_from_server(item)
        update_json(item.path, ret)
        return ret["downloadStatus"]

    # No tenemos server, necesitamos buscar el mejor
    else:
        ret = download_from_best_server(item)
        update_json(item.path, ret)
        return ret["downloadStatus"]


def get_episodes(item):
    logger.info("pelisalacarta.channels.descargas get_episodes")
    
    #El item YA es un episodio, no cal buscar
    if item.contentType == "episode":
      episodes = [item.clone()]
      
    #El item es uma serie o temporada
    elif item.contentType in ["tvshow", "season"]:
      # importamos el canal
      channel = __import__('channels.%s' % item.contentChannel, None, None, ["channels.%s" % item.contentChannel])
      # Obtenemos el listado de episodios
      episodes = getattr(channel, item.contentAction)(item)
    
    itemlist = []
    
    #Tenemos las lista, ahora vamos a comprobar
    for episode in episodes:
      
      #Si partiamos de un item que ya era episodio estos datos ya están bien, no hay que modificarlos
      if item.contentType != "episode":
        episode.contentAction = episode.action
        episode.contentChannel = episode.channel
      
      #Si el resultado es una temporada, no nos vale, tenemos que descargar los episodios de cada temporada
      if episode.contentType == "season":
        itemlist.extend(get_episodes(episode))
      
      #Si el resultado es un episodio ya es lo que necesitamos, lo preparamos para añadirlo a la descarga 
      if episode.contentType == "episode":
        episode.infoLabels = item.infoLabels
        tmdb.find_and_set_infoLabels_tmdb(episode)
        episode.action = "menu"
        episode.channel = "descargas"
        episode.downloadStatus = 0
        episode.downloadProgress = 0
        episode.downloadSize = 0
        episode.downloadCompleted = 0
        if episode.text_color: del episode.text_color
        if episode.text_bold: del episode.text_bold
        if episode.text_italic: del episode.text_italic

        season_and_episode = scrapertools.get_season_and_episode(episode.title)

        if season_and_episode and episode.contentTitle:
            episode.contentSeason, episode.contentEpisodeNumber = season_and_episode.split("x")
            episode.downloadFilename = os.path.join(item.downloadFilename,"%s - %s" %
                                                                      (season_and_episode, episode.contentTitle))
        else:
            episode.contentTitle = re.sub("\[[^\]]+\]|\([^\)]+\)","",episode.title).strip()
            episode.downloadFilename = os.path.join(item.downloadFilename, episode.contentTitle)
            
        itemlist.append(episode)
        
      #Cualquier otro resultado no nos vale, lo ignoramos
      else:
        logger.info("Omitiendo item no válido: %s" % episode.tostring())
        
    return itemlist 


def save_download(item):
    logger.info("pelisalacarta.channels.descargas save_download")
    # Menu contextual
    if item.from_action and item.from_channel:
        item.channel = item.from_channel
        item.action = item.from_action
        del item.from_action
        del item.from_channel

    item.contentChannel = item.channel
    item.contentAction = item.action

    if item.contentType in ["tvshow", "episode", "season"]:
        save_download_tvshow(item)
                
    elif item.contentType == "movie":
        save_download_movie(item)
    
    else:
        logger.error("ContentType no admitido")

def save_download_movie(item):
    logger.info("pelisalacarta.channels.descargas save_download_movie")
    
    progreso = platformtools.dialog_progress("Descargas", "Obteniendo datos de la pelicula")
    tmdb.find_and_set_infoLabels_tmdb(item)
    
    progreso.update(0, "Añadiendo pelicula...")
    
    item.action = "menu"
    item.channel = "descargas"
    item.downloadStatus = 0
    item.downloadProgress = 0
    item.downloadSize = 0
    item.downloadCompleted = 0
    item.downloadFilename = "%s [%s]" % (item.contentTitle, item.contentChannel)
    if item.text_color: del item.text_color
    if item.text_bold: del item.text_bold
    if item.text_italic: del item.text_italic

    item.path = filetools.encode(os.path.join(config.get_setting("downloadlistpath"), str(time.time()) + ".json"))
    filetools.write(item.path, item.tojson())
    
    progreso.close()
    
    if not platformtools.dialog_yesno(config.get_localized_string(30101), "¿Iniciar la descarga ahora?"):
        platformtools.dialog_ok(config.get_localized_string(30101), item.contentTitle,
                                config.get_localized_string(30109))
    else:
        start_download(item)


def save_download_tvshow(item):
    logger.info("pelisalacarta.channels.descargas save_download_tvshow")
    logger.info("Tipo: %s" % item.contentType)
    
    progreso = platformtools.dialog_progress("Descargas", "Obteniendo datos de la serie")
    
    tmdb.find_and_set_infoLabels_tmdb(item)

    item.downloadFilename = item.downloadFilename = "%s [%s]" % (item.contentSerieName, item.contentChannel)
    episodes = get_episodes(item)

    progreso.update(0, "Añadiendo capitulos...")

    for x, i in enumerate(episodes):
        progreso.update(x * 100 / len(episodes), os.path.basename(i.downloadFilename))
        i.path = os.path.join(config.get_setting("downloadlistpath"), str(time.time()) + ".json")
        filetools.write(i.path, i.tojson())
        time.sleep(0.1)

    progreso.close()

    if not platformtools.dialog_yesno(config.get_localized_string(30101), "¿Iniciar la descarga ahora?"):
        platformtools.dialog_ok(config.get_localized_string(30101),
                                str(len(episodes)) + " capitulos de: " + item.contentSerieName,
                                config.get_localized_string(30109))
    else:
        for i in episodes:
            res = start_download(i)
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
                        plot=plot, fanart=thumbnail, extra=os.path.join(savepath, fichero), fulltitle=fulltitle,
                        folder=False)

            # Eliminamos el .txt
            os.remove(item.extra)
            item.extra = ""

            # Guardamos el archivo
            filename = os.path.join(savepath, str(time.time()) + ".json")
            filetools.write(filename, item.tojson())


check_bookmark(config.get_setting("downloadlistpath"))