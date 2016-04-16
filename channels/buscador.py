# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import os
import glob
import time
import imp
import urlparse
import re
import channelselector
from core import config
from core import logger
from core.item import Item
from core import channeltools
from platformcode import platformtools
from threading import Thread


__channel__ = "buscador"

logger.info("pelisalacarta.channels.buscador init")

DEBUG = True


def isGeneric():
    return True


def mainlist(item,preferred_thumbnail="squares"):
    logger.info("pelisalacarta.channels.buscador mainlist")

    itemlist = list()
    itemlist.append(Item(channel=__channel__, action="search", title="Busqueda generica..."))


    itemlist.append(Item(channel=__channel__, action="search", title="Busqueda por categorias...", extra="categorias"))
    itemlist.append(Item(channel=__channel__, action="opciones", title="Opciones"))

    saved_searches_list = get_saved_searches()

    for saved_search_text in saved_searches_list:
        itemlist.append(Item(channel=__channel__, action="do_search", title=' "'+saved_search_text+'"', extra=saved_search_text))

    return itemlist
    
    
def opciones(item):
    itemlist = []
    itemlist.append(Item(channel=__channel__, action="clear_saved_searches", title="Borrar búsquedas guardadas"))
    itemlist.append(Item(channel=__channel__, action="settingCanal", title="Canales incluidos..."))
    itemlist.append(Item(channel=__channel__, action="settings", title="Ajustes buscador"))
    return itemlist
        
def settings(item):
    return platformtools.show_channel_settings()

def settingCanal(item):
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.xml')
    channel_language = config.get_setting("channel_language")

    if channel_language == "":
        channel_language = "all"
    
    list_controls = []
    for infile in sorted(glob.glob(channels_path)):
        channel_name = os.path.basename(infile)[:-4]
        channel_parameters = channeltools.get_channel_parameters(channel_name)
        
        # No incluir si es un canal inactivo
        if channel_parameters["active"] != "true":
            continue
        
        # No incluir si es un canal para adultos, y el modo adulto está desactivado
        if channel_parameters["adult"] == "true" and config.get_setting("adult_mode") == "false":
            continue

        # No incluir si el canal es en un idioma filtrado
        if channel_language != "all" and channel_parameters["language"] != channel_language:
            continue
        
        # No incluir si en la configuracion del canal no existe "include_in_global_search"
        include_in_global_search = config.get_setting("include_in_global_search",channel_name)
        if include_in_global_search == "":
            continue
        
        control = {'id': channel_name,
                      'type': "bool",                    
                      'label': channel_parameters["title"],
                      'default': include_in_global_search,
                      'enabled': True,
                      'visible': True}

        list_controls.append(control)
                
    return platformtools.show_channel_settings(list_controls=list_controls, caption= "Canales incluidos en la búsqueda global", callback="save_settings", item=item)
    
def save_settings(item,dict_values):
  for v in dict_values:
    config.set_setting("include_in_global_search", dict_values[v],v)
    
def searchbycat(item):
    # Only in xbmc/kodi
    # Abre un cuadro de dialogo con las categorías en las que hacer la búsqueda
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.xml')
    channel_language = config.get_setting("channel_language")
    if channel_language == "":
        channel_language = "all"

    categories = [ "Películas","Series","Anime","Documentales","VOS","Latino"]
    categories_id = [ "movie","serie","anime","documentary","vos","latino"]
    list_controls = []
    for i, category in enumerate(categories):
        control = {'id': categories_id[i],
                      'type': "bool",
                      'label': category,
                      'default': False,
                      'enabled': True,
                      'visible': True}

        list_controls.append(control)
    control = {'id': "separador",
                      'type': "label",
                      'label': '',
                      'default': "",
                      'enabled': True,
                      'visible': True}    
    list_controls.append(control)
    control = {'id': "torrent",
                      'type': "bool",
                      'label': 'Incluir en la búsqueda canales Torrent',
                      'default': True,
                      'enabled': True,
                      'visible': True}    
    list_controls.append(control)
                
    return platformtools.show_channel_settings(list_controls=list_controls, caption= "Elegir categorías", callback="search_cb", item=item)

def search_cb(item,values=""):
    cat = []
    for c in values:
      if values[c]:
        cat.append(c)

    if not len(cat):
      return None
    else:
      logger.info(item.tostring())
      logger.info(str(cat))
      return do_search(item, cat)
  
  
# Al llamar a esta función, el sistema pedirá primero el texto a buscar
# y lo pasará en el parámetro "tecleado"
def search(item, tecleado):
    logger.info("pelisalacarta.channels.buscador search")

    if tecleado != "":
        save_search(tecleado)

    if item.extra == "categorias":
        item.extra = tecleado
        return searchbycat(item)

    item.extra = tecleado
    return do_search(item, [])
  
def channel_result(item):
  extra = item.extra.split("{}")[0]
  channel = item.extra.split("{}")[1]
  tecleado = item.extra.split("{}")[2]
  exec "from channels import " + channel + " as module"
  item.channel = channel
  item.extra = extra
  print item.url
  itemlist = module.search(item, tecleado)
  return itemlist

def channel_search(search_results, channel_parameters,tecleado):
    ListaCanales = []
    try:
      exec "from channels import " + channel_parameters["channel"] + " as module"
      mainlist = module.mainlist(Item())
      search_items = [item for item in mainlist if item.action=="search"]
      
      for item in search_items:
            result = module.search(item.clone(), tecleado)
            if result ==None: result = []
            if len(result):
              if not channel_parameters["title"] in search_results:
                search_results[channel_parameters["title"]] = []
              search_results[channel_parameters["title"]].append({"item": item, "itemlist":result})
                

              
    except:
      logger.error("No se puede buscar en: "+ channel_parameters["title"])  
      import traceback
      logger.error(traceback.format_exc())
      
            

# Esta es la función que realmente realiza la búsqueda
def do_search(item, categories=[]):
    multithread = config.get_setting("multithread","buscador")
    result_mode = config.get_setting("result_mode","buscador")
    logger.info("pelisalacarta.channels.buscador do_search")

    tecleado = item.extra

    itemlist = []

    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.xml')
    logger.info("pelisalacarta.channels.buscador channels_path="+channels_path)

    channel_language = config.get_setting("channel_language")
    logger.info("pelisalacarta.channels.buscador channel_language="+channel_language)
    if channel_language == "":
        channel_language = "all"
        logger.info("pelisalacarta.channels.buscador channel_language="+channel_language)

    #Para Kodi es necesario esperar antes de cargar el progreso, de lo contrario
    #el cuadro de progreso queda "detras" del cuadro "cargando..." y no se le puede dar a cancelar
    time.sleep(0.5)
    
    progreso = platformtools.dialog_progress("Buscando " + tecleado,"")


    channel_files = glob.glob(channels_path)
    number_of_channels = len(channel_files)
    
    searches = []
    search_results = {}
    start_time = time.time()
    
    if multithread:
      progreso.update(0, "Buscando %s..." % (tecleado))
      
    for index, infile in enumerate(channel_files):
        percentage = index*100/number_of_channels

        basename = os.path.basename(infile)
        basename_without_extension = basename[:-4]

        channel_parameters = channeltools.get_channel_parameters(basename_without_extension)

        # No busca si es un canal inactivo
        if channel_parameters["active"] != "true":
            continue
        
        # En caso de busqueda por categorias
        if categories:
            if not any(cat in channel_parameters["categories"] for cat in categories):
                continue
                
        # No busca si es un canal para adultos, y el modo adulto está desactivado
        if channel_parameters["adult"] == "true" and config.get_setting("adult_mode") == "false":
            continue

        # No busca si el canal es en un idioma filtrado
        if channel_language != "all" and channel_parameters["language"] != channel_language:
            continue
        
        # No busca si es un canal excluido de la busqueda global
        include_in_global_search = channel_parameters["include_in_global_search"]
        if include_in_global_search == "":
            #Buscar en la configuracion del canal
            include_in_global_search = str(config.get_setting("include_in_global_search",basename_without_extension))
        if include_in_global_search.lower() != "true":
            continue
            
        if progreso.iscanceled(): break
        
        #Modo Multi Thread            
        if multithread:
          t = Thread(target=channel_search,args=[search_results, channel_parameters, tecleado])
          t.setDaemon(True) 
          t.start()
          searches.append(t)
        
        #Modo single Thread
        else:
          logger.info("pelisalacarta.channels.buscador Intentado busqueda en " + basename_without_extension + " de " + tecleado)

          progreso.update(percentage, "Buscando %s en %s..." % (tecleado, channel_parameters["title"]))
          channel_search(search_results, channel_parameters, tecleado)
    

    #Modo Multi Thread
    if multithread :
      pendent =  len([a for a in searches if a.is_alive()])
      while pendent:
        pendent =  len([a for a in searches if a.is_alive()])
        percentage =  (len(searches) - pendent) * 100 / len(searches)
        progreso.update(percentage, "Buscando %s en %d canales..." % (tecleado, len(searches)))
        if progreso.iscanceled(): break
        time.sleep(0.5)
          
    total = 0 
    
    for channel in sorted(search_results.keys()):
      for search in search_results[channel]:
        total+= len(search["itemlist"])
        if result_mode ==0:
            title = channel
            if len(search_results[channel]) > 1:
              title += " [" + search["item"].title.strip() + "]"
            title +=" (" + str(len(search["itemlist"])) + ")"
            
            title = re.sub("\[COLOR [^\]]+\]","",title)
            title = re.sub("\[/COLOR]","",title)
            
            extra = search["item"].extra + "{}" + search["item"].channel + "{}" + tecleado
            itemlist.append(Item(title=title, channel="buscador",action="channel_result", url=search["item"].url, extra = extra, folder=True))
        else:
          itemlist.extend(search["itemlist"])
  
  
  
    title="Buscando: '%s' | Encontrado: %d vídeos | Tiempo: %2.f segundos" % (tecleado,total, time.time()-start_time)
    itemlist.insert(0,Item(title=title, color='yellow'))

    progreso.close()

    return itemlist


def save_search(text):

    saved_searches_limit = int((10, 20, 30, 40, )[int(config.get_setting("saved_searches_limit", "buscador"))])

    saved_searches_list = list(config.get_setting("saved_searches_list", "buscador"))

    if (text + "\n") in saved_searches_list:
        saved_searches_list.remove(text+ "\n")
        
    saved_searches_list.insert(0,text + "\n")
    
    
    config.set_setting("saved_searches_list", saved_searches_list[:saved_searches_limit], "buscador")


def clear_saved_searches(item):
    
    config.set_setting("saved_searches_list", list(), "buscador")


def get_saved_searches():

    saved_searches_list = list(config.get_setting("saved_searches_list", "buscador"))
    
    trimmed = []
    for saved_search_text in saved_searches_list:
        trimmed.append(saved_search_text.strip())
    
    return trimmed
    
    
