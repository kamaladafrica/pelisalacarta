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

STATUS_COLORS = {0: "orange", 1: "orange", 2: "green", 3: "red"}
STATUS_CODES = type("StatusCode",(), {"stoped" : 0, "canceled" : 1 , "completed" : 2, "error" : 3})
DOWNLOAD_LIST_PATH = config.get_setting("downloadlistpath")
TITLE_FILE = "[COLOR %s][%i%%][/COLOR] %s"
TITLE_TVSHOW = "[COLOR %s][%i%%][/COLOR] %s [%s]"


def mainlist(item):
    logger.info("pelisalacarta.channels.descargas mainlist")
    itemlist = []
    
    for file in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if not file.endswith(".json"): continue
        
        file = os.path.join(DOWNLOAD_LIST_PATH, file)
        i = Item(path = file).fromjson(filetools.read(file))
        i.thumbnail = i.contentThumbnail

        #Listado principal
        if not item.contentType == "tvshow":
          # Series
          if i.contentType == "episode":
              if not filter(lambda x: x.contentSerieName == i.contentSerieName and x.contentChannel == i.contentChannel, itemlist):
              
                title = TITLE_TVSHOW % (STATUS_COLORS[i.downloadStatus], i.downloadProgress, i.contentSerieName, i.contentChannel)
                
                itemlist.append(Item(title = title, channel= "descargas", action= "mainlist", contentType = "tvshow", 
                                     contentSerieName = i.contentSerieName, contentChannel = i.contentChannel, 
                                     downloadStatus = i.downloadStatus, downloadProgress = [i.downloadProgress],
                                     fanart = i.fanart, thumbnail = i.thumbnail)) 
              else:
                s = filter(lambda x: x.contentSerieName == i.contentSerieName and x.contentChannel == i.contentChannel, itemlist)[0]
                
                s.downloadProgress.append(i.downloadProgress)
                downloadProgress = sum(s.downloadProgress) / len(s.downloadProgress)
                
                if not s.downloadStatus in [STATUS_CODES.error, STATUS_CODES.canceled] and not i.downloadStatus in [STATUS_CODES.completed, STATUS_CODES.stoped]:
                    s.downloadStatus = i.downloadStatus
                      
                s.title = TITLE_TVSHOW % (STATUS_COLORS[s.downloadStatus], downloadProgress, i.contentSerieName, i.contentChannel)

          # Peliculas
          elif i.contentType == "movie" or i.contentType == "video":
              i.title = TITLE_FILE % (STATUS_COLORS[i.downloadStatus], i.downloadProgress, i.contentTitle)
              itemlist.append(i)
        
        #Listado dentro de una serie      
        else:
            if i.contentType == "episode" and i.contentSerieName == item.contentSerieName and i.contentChannel == item.contentChannel:
            
                  i.title = TITLE_FILE % (STATUS_COLORS[i.downloadStatus], i.downloadProgress, 
                                          "%dx%0.2d: %s" % (i.contentSeason, i.contentEpisodeNumber,i.contentTitle))
                  itemlist.append(i)  

                    
    estados = [i.downloadStatus for i in itemlist]
    

    # Si hay alguno completado
    if 2 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="clean_ready", title="Eliminar descargas completadas",
                                contentType = item.contentType, contentChannel=item.contentChannel, contentSerieName = item.contentSerieName))

    # Si hay alguno con error
    if 3 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="restart_error", title="Reiniciar descargas con error",
                                contentType = item.contentType, contentChannel=item.contentChannel, contentSerieName = item.contentSerieName))

    # Si hay alguno pendiente
    if 1 in estados or 0 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="download_all", title="Descargar todo",
                                contentType = item.contentType, contentChannel=item.contentChannel, contentSerieName = item.contentSerieName))

    if len(itemlist):
        itemlist.insert(0, Item(channel=item.channel, action="clean_all", title="Eliminar todo",
                                contentType = item.contentType, contentChannel=item.contentChannel, contentSerieName = item.contentSerieName))

    return itemlist


def clean_all(item):
    logger.info("pelisalacarta.channels.descargas clean_all")
    
    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        download_item = Item().fromjson(filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))
        if not item.contentType == "tvshow" or (item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
          if fichero.endswith(".json"):
              filetools.remove(os.path.join(DOWNLOAD_LIST_PATH, fichero))

    platformtools.itemlist_refresh()


def clean_ready(item):
    logger.info("pelisalacarta.channels.descargas clean_ready")
    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))
            if not item.contentType == "tvshow" or (item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
              if download_item.downloadStatus == STATUS_CODES.completed:
                  filetools.remove(os.path.join(DOWNLOAD_LIST_PATH, fichero))

    platformtools.itemlist_refresh()


def restart_error(item):
    logger.info("pelisalacarta.channels.descargas restart_error")
    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))
            
            if not item.contentType == "tvshow" or (item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
              if download_item.downloadStatus == STATUS_CODES.error:
                  if filetools.isfile(os.path.join(config.get_setting("downloadpath"), download_item.downloadFilename)):
                      filetools.remove(os.path.join(config.get_setting("downloadpath"), download_item.downloadFilename))
                      
                  update_json(item.path, {"downloadStatus" : STATUS_CODES.stoped, "downloadComplete" :  0 , "downloadProgress" : 0, "downloadUrl" : ""})


    platformtools.itemlist_refresh()


def download_all(item):
    time.sleep(0.5)
    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))

            if not item.contentType == "tvshow" or (item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
              download_item.path = os.path.join(DOWNLOAD_LIST_PATH, fichero)
              if download_item.downloadStatus in [STATUS_CODES.stoped, STATUS_CODES.canceled]:
                  res = start_download(download_item)
                  platformtools.itemlist_refresh()
                  # Si se ha cancelado paramos
                  if res == STATUS_CODES.canceled: break


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
            
        update_json(item.path, {"downloadStatus" : STATUS_CODES.stoped, "downloadComplete" :  0 , "downloadProgress" : 0, "downloadUrl" : ""})

    platformtools.itemlist_refresh()


def move_to_libray(item):
    try:
      from platformcode import library
    except:
      return
      
    # Copiamos el archivo a la biblioteca
    origen = filetools.join(config.get_setting("downloadpath"), item.downloadFilename)
    destino = filetools.join(config.get_library_path(), *filetools.split(item.downloadFilename))
    
    if not filetools.isdir(filetools.dirname(destino)):
      filetools.mkdir(filetools.dirname(destino))
    
    if filetools.isfile(destino) and filetools.isfile(origen) :
      filetools.remove(destino)

    if filetools.isfile(origen):
      filetools.move(origen, destino)
      if len(filetools.listdir(filetools.dirname(origen))) == 0: 
        filetools.rmdir(filetools.dirname(origen))
      
    else:
      logger.error("No se ha encontrado el archivo: %s" % origen)
    
    if filetools.isfile(destino):
      if item.contentType == "movie":
        library_item = Item(title="Descargado: %s" % item.downloadFilename, channel= "descargas", action="findvideos", infoLabels=item.infoLabels, url=destino)
        
        library.save_library_movie(library_item)
        
      elif item.contentType == "episode":
        library_item = Item(title="Descargado: %s" % item.downloadFilename, channel= "descargas", action="findvideos", infoLabels=item.infoLabels, url=destino)
        
        tvshow = Item(channel= "descargas", contentType="tvshow", infoLabels = {"tmdb_id": item.infoLabels["tmdb_id"]})
        library.save_library_tvshow(tvshow, [library_item])



def update_json(path, params):
    item = Item().fromjson(filetools.read(path))
    item.__dict__.update(params)
    filetools.write(path, item.tojson())



def sort_metod(item):
    """
    Puntua cada item en función de la calidad del vídeo, buscando la calidad en el titulo mediante un listado de calidades predefinidas
    y ordenadas de mejor a peor. Si no se encuentra ninguna calidad de la lista, se coloca en ultimo lugar
    @type item: item
    @param item: elemento que se va a valorar.
    @return:  puntuacion otenida
    @rtype: int
    """
    import re

    # TODO: completar lista
    # List con el orden de calidades (de mejor a peor)
    # Espacios es equivalente a " " o "-"
    # Da igual mayusculas
    full_hd_names = ["FULLHD", "1080P"]
    hd_names = ["HD", "HD 720", "HD REAL 720", "MICROHD", "720P", "HDTV"]
    sd_names = ["SD", "480P", "360P", "240P"]
    calidades = full_hd_names + hd_names + sd_names

    re_calidades = "|".join(calidades)
    calidad = re.compile("(?:\(|\[|\s|^)(" + re_calidades + ")(?:\)|\]|\s|$)", re.IGNORECASE).findall(item.title)
    if calidad: calidad = calidades.index(calidad[-1].upper())
    else: calidad = len(calidades)*10


    idiomas = ["CAST", "ESP", "LAT", "VOSE"]

    re_idiomas = "|".join(idiomas)
    idioma = re.compile("(?:\(|\[|\s|^)(" + re_idiomas + ")(?:\)|\]|\s|$)", re.IGNORECASE).findall(item.title)
    if idioma: idioma = idiomas.index(idioma[-1].upper()) *10
    else: idioma = len(idiomas)*10

 
    return idioma + calidad
        

def download_from_url(url, item):
    logger.info("pelisalacarta.channels.descargas download_from_url - Intentando descargar: %s" % (url))

    # Obtenemos la ruta de descarga y el nombre del archivo
    download_path = filetools.dirname(filetools.join(config.get_setting("downloadpath"), item.downloadFilename))
    file_name = filetools.basename(filetools.join(config.get_setting("downloadpath"), item.downloadFilename))

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
        status = STATUS_CODES.error

    # Aun está descargando (se ha hecho click en cancelar)
    elif d.state == d.states.downloading:
        logger.info("pelisalacarta.channels.descargas download_video - Descarga detenida")
        d.stop()
        progreso.close()
        status = STATUS_CODES.canceled

    # La descarga ha finalizado
    elif d.state == d.states.completed:
        logger.info("pelisalacarta.channels.descargas download_video - Descargado correctamente")
        progreso.close()
        status = STATUS_CODES.completed

        if item.downloadSize and item.downloadSize != d.size[0]:
            status = STATUS_CODES.error

    
    if progreso.iscanceled():
      status = STATUS_CODES.canceled
      
    dir = os.path.dirname(item.downloadFilename)
    file = filetools.join(dir, filetools.decode(d.filename))
    
    if status == STATUS_CODES.completed:
        move_to_libray(item.clone(downloadFilename =  file))
        
    return {"downloadUrl": d.download_url, "downloadStatus": status, "downloadSize": d.size[0],
            "downloadProgress": d.progress, "downloadCompleted": d.downloaded[0], "downloadFilename": file}


def download_from_server(item):
    unsupported_servers = ["torrent"]
    
    if item.server:
        logger.info("contentAction: %s | contentChannel: %s | server: %s | url: %s" % (item.contentAction, item.contentChannel, item.server, item.url))
        
    #Si ya tenemos server no hace falta play, probablemente venimos del menu de reproduccion
    if not item.server:
        progreso = platformtools.dialog_progress("Descargas", "Obteniendo enlaces")

        channel = __import__('channels.%s' % item.contentChannel, None, None, ["channels.%s" % item.contentChannel])
        if hasattr(channel, "play"):
            progreso.update(50, "Obteniendo enlaces.", "Conectando con %s..." % item.contentChannel)
            itemlist = getattr(channel, "play")(item)
            if len(itemlist):
                download_item = item.clone(**itemlist[0].__dict__)
                download_item.contentAction = download_item.action
                download_item.infoLabels = item.infoLabels
                item = download_item
                logger.info("contentAction: %s | contentChannel: %s | server: %s | url: %s" % (item.contentAction, item.contentChannel, item.server, item.url))

            else:
                logger.info("No hay nada que reproducir")
                return {"downloadStatus": STATUS_CODES.error}

        progreso.close()
    
    if not item.server or not item.url or not item.contentAction == "play" or item.server in unsupported_servers:
      logger.error("El Item no contiene los parametros necesarios.")
      return {"downloadStatus": STATUS_CODES.error}
      
    video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(item.server, item.url, item.password, True)

     # Si no esta disponible, salimos
    if not puedes:
        logger.info("El vídeo **NO** está disponible")
        return {"downloadStatus": STATUS_CODES.error}

    else:
        logger.info("El vídeo **SI** está disponible")

        result = {}

        # Recorre todas las opciones hasta que consiga descargar una correctamente
        for video_url in reversed(video_urls):
            if video_url[1].lower().endswith(".m3u8"):
              result["downloadStatus"] = STATUS_CODES.error
              continue
            
            result = download_from_url(video_url[1], item)

            if result["downloadStatus"] in [STATUS_CODES.canceled, STATUS_CODES.completed]:
                break
                
            # Error en la descarga, continuamos con la siguiente opcion
            if result["downloadStatus"] == STATUS_CODES.error:
                continue

        # Devolvemos el estado
        return result


def download_from_best_server(item):
    logger.info("contentAction: %s | contentAction: %s | url: %s" % (item.contentAction, item.contentAction, item.url))
    result =  {"downloadStatus": STATUS_CODES.error}

    progreso = platformtools.dialog_progress("Descargas", "Obteniendo lista de servidores disponibles...")

    channel = __import__('channels.%s' % item.contentChannel, None, None, ["channels.%s" % item.contentChannel])
    
    progreso.update(50, "Obteniendo lista de servidores disponibles.", "Conectando con %s..." % item.contentChannel)
    if hasattr(channel, item.contentAction):
        play_items = getattr(channel, item.contentAction)(item.clone(action = item.contentAction, channel = item.contentChannel))
    else:
        play_items = servertools.find_video_items(item.clone(action = item.contentAction, channel = item.contentChannel))
   
    play_items = filter(lambda x: x.action == "play", play_items)
    for it in play_items:
      print it.title
    play_items.sort(key=sort_metod)
    print "--------------------"
    for it in play_items:
      print it.title
      
    progreso.update(100, "Obteniendo lista de servidores disponibles.", "Servidores disponibles: %s" % len(play_items))

    if progreso.iscanceled():
        return {"downloadStatus": STATUS_CODES.canceled}
          
    time.sleep(0.5)
    progreso.close()
    
    
    # Recorremos el listado de servers, hasta encontrar uno que funcione
    for play_item in play_items:
        play_item = item.clone(**play_item.__dict__)
        play_item.contentAction = play_item.action
        play_item.infoLabels = item.infoLabels

        result = download_from_server(play_item)
        
        if progreso.iscanceled():
          result["downloadStatus"] = STATUS_CODES.canceled

        # Tanto si se cancela la descarga como si se completa dejamos de probar mas opciones
        if result["downloadStatus"] in [STATUS_CODES.canceled, STATUS_CODES.completed]:
            break
            
    return result


def start_download(item):
    logger.info("contentAction: %s | conentChannel: %s | url: %s" % (item.contentAction, item.conentChannel, item.url))

    # Descarga pausada, intentamos continuar con la misma url
    if item.downloadStatus == STATUS_CODES.canceled and item.downloadUrl:
        ret = download_from_url(item.downloadUrl, item)
        if ret["downloadStatus"] != STATUS_CODES.error:
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
    logger.info("contentAction: %s | contentChannel: %s | contentType: %s" % (item.contentAction, item.contentChannel, item.contentType))
    
    #El item que pretendemos descargar YA es un episodio
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
        
        #Pasamos el id al episodio
        if not episode.infoLabels["tmdb_id"]:
          episode.infoLabels["tmdb_id"] = item.infoLabels["tmdb_id"]
          
        #Buscamos en tmdb
        tmdb.find_and_set_infoLabels_tmdb(episode)
                
        #Episodio, Temporada y Titulo
        if not episode.contentSeason or not episode.contentEpisodeNumber or not episode.contentTitle:
          season_and_episode = scrapertools.get_season_and_episode(episode.title)
          episode_title = episode.title.replace(season_and_episode, "").strip(": -")
          
          if not episode.contentSeason: episode.contentSeason = season_and_episode.split("x")[0]
          if not episode.contentEpisodeNumber: episode.contentEpisodeNumber = season_and_episode.split("x")[1]
          if not episode.contentTitle: episode.contentTitle = episode_title
          
        episode.downloadFilename = os.path.join(item.downloadFilename,"%dx%0.2d - %s" % (episode.contentSeason, episode.contentEpisodeNumber, episode.contentTitle.strip()))
        
        itemlist.append(episode)
      #Cualquier otro resultado no nos vale, lo ignoramos
      else:
        logger.info("Omitiendo item no válido: %s" % episode.tostring())
        
    return itemlist 

def write_json(item):
      logger.info("pelisalacarta.channels.descargas write_json")
    
      item.action = "menu"
      item.channel = "descargas"
      item.downloadStatus = STATUS_CODES.stoped
      item.downloadProgress = 0
      item.downloadSize = 0
      item.downloadCompleted = 0
      if not item.contentThumbnail:
        item.contentThumbnail = item.thumbnail
      
      for name in ["text_bold", "text_color", "text_italic", "context", "totalItems", "viewmode", "title", "fulltitle", "thumbnail"]:
        if item.__dict__.has_key(name):
          item.__dict__.pop(name)

      path = filetools.encode(os.path.join(config.get_setting("downloadlistpath"), str(time.time()) + ".json"))
      filetools.write(path, item.tojson())
      item.path = path
      time.sleep(0.1)

    
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
    
    elif item.contentType == "video":
        save_download_video(item)
    else:
        logger.error("ContentType no admitido")

def save_download_video(item):
    logger.info("contentAction: %s | contentChannel: %s | contentTitle: %s" % (item.contentAction, item.contentChannel, item.contentTitle))
    progreso = platformtools.dialog_progress("Descargas", "Añadiendo video...")
    

    if not item.contentTitle:
      item.contentTitle = re.sub("\[[^\]]+\]|\([^\)]+\)","",item.fulltitle).strip()
      
    if not item.contentTitle:
      item.contentTitle = re.sub("\[[^\]]+\]|\([^\)]+\)","",item.title).strip()
      
    item.downloadFilename = "%s [%s]" % (item.contentTitle.strip(), item.contentChannel)

    write_json(item)

    progreso.close()
    
    if not platformtools.dialog_yesno(config.get_localized_string(30101), "¿Iniciar la descarga ahora?"):
        platformtools.dialog_ok(config.get_localized_string(30101), item.contentTitle,
                                config.get_localized_string(30109))
    else:
        start_download(item)


def save_download_movie(item):
    logger.info("contentAction: %s | contentChannel: %s | contentTitle: %s" % (item.contentAction, item.contentChannel, item.contentTitle))
    
    progreso = platformtools.dialog_progress("Descargas", "Obteniendo datos de la pelicula")
    
    result = tmdb.find_and_set_infoLabels_tmdb(item)
    if not result:
      progreso.close()
      item.contentType = "video"
      return save_download_video(item)
    
    progreso.update(0, "Añadiendo pelicula...")

    item.downloadFilename = "%s [%s]" % (item.contentTitle.strip(), item.contentChannel)

    write_json(item)

    progreso.close()
    
    if not platformtools.dialog_yesno(config.get_localized_string(30101), "¿Iniciar la descarga ahora?"):
        platformtools.dialog_ok(config.get_localized_string(30101), item.contentTitle,
                                config.get_localized_string(30109))
    else:
        start_download(item)


def save_download_tvshow(item):
    logger.info("contentAction: %s | contentChannel: %s | contentType: %s | contentSerieName: %s" % (item.contentAction, item.contentChannel, item.contentType, item.contentSerieName))
    
    progreso = platformtools.dialog_progress("Descargas", "Obteniendo datos de la serie")
    
    tmdb.find_and_set_infoLabels_tmdb(item)
    
    item.downloadFilename = item.downloadFilename = "%s [%s]" % (item.contentSerieName, item.contentChannel)
    
    progreso.update(0, "Obteniendo episodios...", "conectando con %s..." % item.contentChannel)

    episodes = get_episodes(item)

    progreso.update(0, "Añadiendo capitulos...", " ")

    for x, i in enumerate(episodes):
        progreso.update(x * 100 / len(episodes), "%dx%0.2d: %s" % (i.contentSeason, i.contentEpisodeNumber, i.contentTitle))
        write_json(i)
    progreso.close()

    if not platformtools.dialog_yesno(config.get_localized_string(30101), "¿Iniciar la descarga ahora?"):
        platformtools.dialog_ok(config.get_localized_string(30101),
                                str(len(episodes)) + " capitulos de: " + item.contentSerieName,
                                config.get_localized_string(30109))
    else:
        for i in episodes:
            res = start_download(i)
            if res == STATUS_CODES.canceled:
                break

