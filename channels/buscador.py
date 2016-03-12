# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

import os
import glob
import imp
from core import config
from core import logger
from core.item import Item
from core import channeltools
from platformcode import guitools


__channel__ = "buscador"

logger.info("pelisalacarta.channels.buscador init")

DEBUG = True


def isGeneric():
    return True


def mainlist(item,preferred_thumbnail="squares"):
    logger.info("pelisalacarta.channels.buscador mainlist")

    itemlist = list()
    itemlist.append(Item(channel=__channel__, action="search", title="Búsqueda genérica..."))

    if config.is_xbmc():
        itemlist.append(Item(channel=__channel__, action="search", title="Búsqueda por categorías...", extra="categorias"))

    saved_searches_list = get_saved_searches()

    for saved_search_text in saved_searches_list:
        itemlist.append(Item(channel=__channel__, action="do_search", title=' "'+saved_search_text+'"',
                             extra=saved_search_text))

    if len(saved_searches_list) > 0:
        itemlist.append(Item(channel=__channel__, action="clear_saved_searches", title="Borrar búsquedas guardadas"))
    
    if config.is_xbmc():
        itemlist.append(Item(channel=__channel__, action="settingCanal", title="Canales incluidos..."))

    return itemlist

def settingCanal(item):
    # Only in xbmc/kodi
    # Abre un cuadro de dialogo con todos los canales q pueden incluirse en la busqueda global para su configuracion
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
                
    ventana = guitools.SettingWindow(list_controls, caption= "Canales incluidos en la búsqueda global")
    ventana.doModal()
    if ventana.isConfirmed():
        for canal, value in ventana.get_values().items():
            config.set_setting("include_in_global_search",value,canal)
    
    
def searchbycat():
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
                
    ventana = guitools.SettingWindow(list_controls, caption= "Elegir categorías")
    ventana.doModal()
    if ventana.isConfirmed():
        cat = []
        for category, value in ventana.get_values().items():
            if value:
                cat.append(category)
        return cat
    else: return False
        
# Al llamar a esta función, el sistema pedirá primero el texto a buscar
# y lo pasará en el parámetro "tecleado"
def search(item, tecleado):
    logger.info("pelisalacarta.channels.buscador search")

    if tecleado != "":
        save_search(tecleado)

    if item.extra == "categorias":
        categories = searchbycat()
        if not categories: return
    else: categories = []

    item.extra = tecleado
    return do_search(item, categories)


# Esta es la función que realmente realiza la búsqueda
def do_search(item, categories=[]):
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

    show_dialog = False
    progreso = None
    if config.is_xbmc():
        show_dialog = True

    try:
        import xbmcgui
        progreso = xbmcgui.DialogProgressBG()
        progreso.create("Buscando " + tecleado.title())
    except ImportError:
        xbmcgui = None
        show_dialog = False

    channel_files = glob.glob(channels_path)
    number_of_channels = len(channel_files)

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
            
        if show_dialog:
            progreso.update(percentage, ' Buscando "' + tecleado + '"', basename_without_extension)

        logger.info("pelisalacarta.channels.buscador Intentado busqueda en " + basename_without_extension + " de " +
                    tecleado)
        try:

            # http://docs.python.org/library/imp.html?highlight=imp#module-imp
            obj = imp.load_source(basename_without_extension, infile[:-4]+".py")
            logger.info("pelisalacarta.channels.buscador cargado " + basename_without_extension + " de " + infile)
            channel_result_itemlist = obj.search(Item(), tecleado)
            for item in channel_result_itemlist:
                item.title = item.title + "[" + basename_without_extension + "]"
                item.viewmode = "list"
                
            channel_result_itemlist = sorted(channel_result_itemlist, key=lambda Item: Item.title) 
            itemlist.extend(channel_result_itemlist)
        except:
            import traceback
            logger.error(traceback.format_exc())

    if show_dialog:
        progreso.close()

    return itemlist


def save_search(text):

    saved_searches_limit = (10, 20, 30, 40, )[int(config.get_setting("saved_searches_limit"))]

    infile= os.path.join(config.get_data_path(), "saved_searches.txt")
    if os.path.exists(infile):
        f = open(infile, "r")
        saved_searches_list = f.readlines()
        f.close()
    else:
        saved_searches_list = []
        
    if (text + "\n") in saved_searches_list:
        saved_searches_list.remove(text+ "\n")
        
    saved_searches_list.insert(0,text + "\n")

    f = open(infile, "w")
    f.writelines(saved_searches_list)
    f.close()


def clear_saved_searches(item):

    f = open(os.path.join(config.get_data_path(), "saved_searches.txt"), "w")
    f.write("")
    f.close()


def get_saved_searches():

    if os.path.exists(os.path.join(config.get_data_path(), "saved_searches.txt")):
        f = open(os.path.join(config.get_data_path(), "saved_searches.txt"), "r")
        saved_searches_list = f.readlines()
        f.close()
    else:
        saved_searches_list = []

    trimmed = []
    for saved_search_text in saved_searches_list:
        trimmed.append(saved_search_text.strip())
    
    return trimmed
