# -*- coding: utf-8 -*-
#------------------------------------------------------------
# tvalacarta
# XBMC Launcher (xbmc / xbmc-dharma / boxee)
# http://blog.tvalacarta.info/plugin-xbmc/
#------------------------------------------------------------

import urllib
import urllib2
import os
import re
import sys
from core.item import Item
from core import logger
from core import config
from core import scrapertools
from core import channeltools
from core import updater
from platformcode import platformtools
from platformcode import xbmctools

def start():
    ''' Primera funcion que se ejecuta al entrar en el plugin.
    Dentro de esta funcion deberian ir todas las llamadas a las
    funciones que deseamos que se ejecuten nada mas abrir el plugin.

    '''
    logger.info("pelisalacarta.platformcode.launcher start")

    # Test if all the required directories are created
    config.verify_directories_created()

def run():
    logger.info("pelisalacarta.platformcode.launcher run")

    # Extract item from sys.argv
    if sys.argv[2]:
      item = Item().fromurl(sys.argv[2])
      params = ""

    else:
      item = Item(action= "selectchannel")
      params = ""

    logger.info(item.tostring())

    server_white_list = []
    server_black_list = []
    if config.get_setting('filter_servers') == 'true':
        server_white_list, server_black_list = set_server_list()

    try:
        # Default action: open channel and launch mainlist function
        if ( item.action=="selectchannel" ):
            import channelselector
            itemlist = channelselector.mainlist(params, item.url, item.category)
            
            # Verifica actualizaciones solo en el primer nivel
            if config.get_setting("updatecheck2") == "true":
              logger.info("channelselector.mainlist Verificar actualizaciones activado")
              from core import updater
              try:
                version = updater.checkforupdates()
                
                if version:
                  import xbmcgui
                  advertencia = xbmcgui.Dialog()
                  advertencia.ok("VersiÃ³n "+version+" disponible","Ya puedes descargar la nueva versiÃ³n del plugin\ndesde el listado principal")
                  itemlist.insert(0,Item(title="Descargar version "+version, version=version, channel="updater", action="update", thumbnail=channelselector.get_thumbnail_path() + "Crystal_Clear_action_info.png"))
              except:
                import xbmcgui
                advertencia = xbmcgui.Dialog()
                advertencia.ok("No se puede conectar","No ha sido posible comprobar","si hay actualizaciones")
                logger.info("channelselector.mainlist Fallo al verificar la actualizaciÃ³n")

            else:
              logger.info("channelselector.mainlist Verificar actualizaciones desactivado")
                
            from platformcode import xbmctools
            xbmctools.renderItems(itemlist, item)

        # Actualizar version
        elif ( item.action=="update" ):
            try:
                from core import updater
                updater.update(params)
            except ImportError:
                logger.info("pelisalacarta.platformcode.launcher Actualizacion automÃ¡tica desactivada")

            #import channelselector as plugin
            #plugin.listchannels(params, url, category)
            if config.get_system_platform()!="xbox":
                import xbmc
                xbmc.executebuiltin( "Container.Refresh" )

        elif (item.action=="channeltypes"):
            import channelselector
            itemlist = channelselector.channeltypes(params,item.url,item.category)
            from platformcode import xbmctools
            xbmctools.renderItems(itemlist, item)

        elif (item.action=="listchannels"):
            import channelselector
            itemlist = channelselector.listchannels(params,item.url,item.category)
            from platformcode import xbmctools
            xbmctools.renderItems(itemlist, item)

        # El resto de acciones vienen en el parÃ¡metro "action", y el canal en el parÃ¡metro "channel"
        else:

            if item.action=="mainlist":
                # Parental control
                can_open_channel = False

                # If it is an adult channel, and user has configured pin, asks for it
                if channeltools.is_adult(item.channel) and config.get_setting("adult_pin")!="":

                    import xbmc
                    keyboard = xbmc.Keyboard("","PIN para canales de adultos",True)
                    keyboard.doModal()

                    if (keyboard.isConfirmed()):
                        tecleado = keyboard.getText()
                        if tecleado==config.get_setting("adult_pin"):
                            can_open_channel = True

                # All the other cases can open the channel
                else:
                    can_open_channel = True

                if not can_open_channel:
                    return

            if item.action=="mainlist" and config.get_setting("updatechannels")=="true":
                try:
                    from core import updater
                    actualizado = updater.updatechannel(item.channel)

                    if actualizado:
                        import xbmcgui
                        advertencia = xbmcgui.Dialog()
                        advertencia.ok("plugin",channel_name,config.get_localized_string(30063))
                except:
                    pass

            # La acciÃ³n puede estar en el core, o ser un canal regular. El buscador es un canal especial que estÃ¡ en pelisalacarta
            regular_channel_path = os.path.join(config.get_runtime_path(), 'channels', item.channel+".py")
            core_channel_path = os.path.join(config.get_runtime_path(), 'core', item.channel+".py")
            logger.info("pelisalacarta.platformcode.launcher regular_channel_path=%s" % regular_channel_path)
            logger.info("pelisalacarta.platformcode.launcher core_channel_path=%s" % core_channel_path)

            if (item.channel == "personal" or item.channel == "personal2" or item.channel == "personal3" or
                    item.channel == "personal4" or item.channel == "personal5"):
                import channels.personal as channel
            elif os.path.exists(regular_channel_path):
                channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])

            elif os.path.exists(core_channel_path):
                channel = __import__('core.%s' % item.channel, fromlist=["core.%s" % item.channel])

            logger.info("pelisalacarta.platformcode.launcher running channel {0} {1}".format(
                channel.__name__, channel.__file__))

            generico = False
            # Esto lo he puesto asi porque el buscador puede ser generico o normal, esto estarÃ¡ asi hasta que todos los canales sean genericos
            if item.category == "Buscador_Generico":
                generico = True
            else:
                try:
                    generico = channel.isGeneric()
                except:
                    generico = False

            if not generico:
                logger.info("pelisalacarta.platformcode.launcher xbmc native channel")
                if item.action == "strm":
                    from platformcode import xbmctools
                    xbmctools.playstrm(params, item.url, item.category)
                else:
                    getattr(channel, item.action)(params, item.url, item.category)
            else:
                logger.info("pelisalacarta.platformcode.launcher multiplatform channel")

                from platformcode import xbmctools

                if item.action=="play":
                    logger.info("pelisalacarta.platformcode.launcher play")
                    # Si el canal tiene una acciÃ³n "play" tiene prioridad
                    if hasattr(channel, 'play'):
                        logger.info("pelisalacarta.platformcode.launcher executing channel 'play' method")
                        itemlist = channel.play(item)
                        if len(itemlist)>0:
                            item = itemlist[0]
                            xbmctools.play_video(item)
                        else:
                            import xbmcgui
                            ventana_error = xbmcgui.Dialog()
                            ok = ventana_error.ok ("plugin", "No hay nada para reproducir")
                    else:
                        logger.info("pelisalacarta.platformcode.launcher no channel 'play' method, executing core method")
                        xbmctools.play_video(item)

                elif item.action == "play_from_library":
                    play_from_library(item, channel, server_white_list, server_black_list)

                elif item.action == "add_pelicula_to_library":
                    add_pelicula_to_library(item)

                elif item.action == "add_serie_to_library":
                    add_serie_to_library(item, channel)

                elif item.action=="download_all_episodes":
                    download_all_episodes(item,channel)

                elif item.action=="search":
                    logger.info("pelisalacarta.platformcode.launcher search")
                    import xbmc
                    keyboard = xbmc.Keyboard("")
                    keyboard.doModal()
                    if (keyboard.isConfirmed()):
                        tecleado = keyboard.getText()
                        tecleado = tecleado.replace(" ", "+")
                        itemlist = channel.search(item,tecleado)
                    else:
                        itemlist = []
                    xbmctools.renderItems(itemlist, item)

                else:
                    logger.info("pelisalacarta.platformcode.launcher executing channel '"+item.action+"' method")
                    if item.action != "findvideos":
                        itemlist = getattr(channel, item.action)(item)
                    else:

                        # Intenta ejecutar una posible funcion "findvideos" del canal
                        if hasattr(channel, 'findvideos'):
                            itemlist = getattr(channel, item.action)(item)

                            if config.get_setting('filter_servers') == 'true':
                                itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

                        # Si no funciona, lanza el mÃ©todo genÃ©rico para detectar vÃ­deos
                        else:
                            logger.info("pelisalacarta.platformcode.launcher no channel 'findvideos' method, executing core method")
                            from core import servertools
                            itemlist = servertools.find_video_items(item)
                            if config.get_setting('filter_servers') == 'true':
                                itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

                        from platformcode import subtitletools
                        subtitletools.saveSubtitleName(item)

                    # Activa el modo biblioteca para todos los canales genÃ©ricos, para que se vea el argumento
                    import xbmcplugin

                    handle = sys.argv[1]
                    xbmcplugin.setContent(int( handle ),"movies")

                    # AÃ±ade los items a la lista de XBMC
                    if type(itemlist) == list:
                      xbmctools.renderItems(itemlist, item)

    except urllib2.URLError,e:
        import traceback
        from pprint import pprint
        exc_type, exc_value, exc_tb = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        for line in lines:
            line_splits = line.split("\n")
            for line_split in line_splits:
                logger.error(line_split)

        import xbmcgui
        ventana_error = xbmcgui.Dialog()
        # Agarra los errores surgidos localmente enviados por las librerias internas
        if hasattr(e, 'reason'):
            logger.info("Razon del error, codigo: %d , Razon: %s" %(e.reason[0],e.reason[1]))
            texto = config.get_localized_string(30050) # "No se puede conectar con el sitio web"
            ok = ventana_error.ok ("plugin", texto)
        # Agarra los errores con codigo de respuesta del servidor externo solicitado
        elif hasattr(e,'code'):
            logger.info("codigo de error HTTP : %d" %e.code)
            texto = (config.get_localized_string(30051) % e.code) # "El sitio web no funciona correctamente (error http %d)"
            ok = ventana_error.ok ("plugin", texto)

            
def episodio_ya_descargado(show_title,episode_title):

    ficheros = os.listdir( "." )

    for fichero in ficheros:
        #logger.info("fichero="+fichero)
        if fichero.lower().startswith(show_title.lower()) and scrapertools.find_single_match(fichero,"(\d+x\d+)")==episode_title:
            logger.info("encontrado!")
            return True

    return False

def set_server_list():
    logger.info("pelisalacarta.platformcode.launcher.set_server_list start")
    server_white_list = []
    server_black_list = []

    if len(config.get_setting('whitelist')) > 0:
        server_white_list_key = config.get_setting('whitelist').replace(', ', ',').replace(' ,', ',')
        server_white_list = re.split(',', server_white_list_key)

    if len(config.get_setting('blacklist')) > 0:
        server_black_list_key = config.get_setting('blacklist').replace(', ', ',').replace(' ,', ',')
        server_black_list = re.split(',', server_black_list_key)

    logger.info("set_server_list whiteList %s" % server_white_list)
    logger.info("set_server_list blackList %s" % server_black_list)
    logger.info("pelisalacarta.platformcode.launcher.set_server_list end")

    return server_white_list, server_black_list

def filtered_servers(itemlist, server_white_list, server_black_list):
    logger.info("pelisalacarta.platformcode.launcher.filtered_servers start")
    new_list = []
    white_counter = 0
    black_counter = 0

    logger.info("filtered_servers whiteList %s" % server_white_list)
    logger.info("filtered_servers blackList %s" % server_black_list)

    if len(server_white_list) > 0:
        logger.info("filtered_servers whiteList")
        for item in itemlist:
            logger.info("item.title " + item.title)
            if any(server in item.title for server in server_white_list):
                # if item.title in server_white_list:
                logger.info("found")
                new_list.append(item)
                white_counter += 1
            else:
                logger.info("not found")

    if len(server_black_list) > 0:
        logger.info("filtered_servers blackList")
        for item in itemlist:
            logger.info("item.title " + item.title)
            if any(server in item.title for server in server_black_list):
                # if item.title in server_white_list:
                logger.info("found")
                black_counter += 1
            else:
                new_list.append(item)
                logger.info("not found")

    logger.info("whiteList server %s has #%d rows" % (server_white_list, white_counter))
    logger.info("blackList server %s has #%d rows" % (server_black_list, black_counter))

    if len(new_list) == 0:
        new_list = itemlist
    logger.info("pelisalacarta.platformcode.launcher.filtered_servers end")

    return new_list

def download_all_episodes(item,channel,first_episode="",preferred_server="vidspot",filter_language=""):
    logger.info("pelisalacarta.platformcode.launcher download_all_episodes, show="+item.show)
    show_title = item.show

    # Obtiene el listado desde el que se llamÃ³
    action = item.extra

    # Esta marca es porque el item tiene algo mÃ¡s aparte en el atributo "extra"
    if "###" in item.extra:
        action = item.extra.split("###")[0]
        item.extra = item.extra.split("###")[1]

    episode_itemlist = getattr(channel, action)(item)

    # Ordena los episodios para que funcione el filtro de first_episode
    episode_itemlist = sorted(episode_itemlist, key=lambda Item: Item.title)

    from core import servertools
    from core import downloadtools
    from core import scrapertools

    best_server = preferred_server
    worst_server = "moevideos"

    # Para cada episodio
    if first_episode=="":
        empezar = True
    else:
        empezar = False

    for episode_item in episode_itemlist:
        try:
            logger.info("pelisalacarta.platformcode.launcher download_all_episodes, episode="+episode_item.title)
            episode_title = scrapertools.get_match(episode_item.title,"(\d+x\d+)")
            logger.info("pelisalacarta.platformcode.launcher download_all_episodes, episode="+episode_title)
        except:
            import traceback
            logger.info(traceback.format_exc())
            continue

        if first_episode!="" and episode_title==first_episode:
            empezar = True

        if episodio_ya_descargado(show_title,episode_title):
            continue

        if not empezar:
            continue

        # Extrae los mirrors
        try:
            mirrors_itemlist = channel.findvideos(episode_item)
        except:
            mirrors_itemlist = servertools.find_video_items(episode_item)
        print mirrors_itemlist

        descargado = False

        new_mirror_itemlist_1 = []
        new_mirror_itemlist_2 = []
        new_mirror_itemlist_3 = []
        new_mirror_itemlist_4 = []
        new_mirror_itemlist_5 = []
        new_mirror_itemlist_6 = []

        for mirror_item in mirrors_itemlist:

            # Si estÃ¡ en espaÃ±ol va al principio, si no va al final
            if "(EspaÃ±ol)" in mirror_item.title:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_1.append(mirror_item)
                else:
                    new_mirror_itemlist_2.append(mirror_item)
            elif "(Latino)" in mirror_item.title:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_3.append(mirror_item)
                else:
                    new_mirror_itemlist_4.append(mirror_item)
            elif "(VOS)" in mirror_item.title:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_3.append(mirror_item)
                else:
                    new_mirror_itemlist_4.append(mirror_item)
            else:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_5.append(mirror_item)
                else:
                    new_mirror_itemlist_6.append(mirror_item)

        mirrors_itemlist = new_mirror_itemlist_1 + new_mirror_itemlist_2 + new_mirror_itemlist_3 + new_mirror_itemlist_4 + new_mirror_itemlist_5 + new_mirror_itemlist_6

        for mirror_item in mirrors_itemlist:
            logger.info("pelisalacarta.platformcode.launcher download_all_episodes, mirror="+mirror_item.title)

            if "(EspaÃ±ol)" in mirror_item.title:
                idioma="(EspaÃ±ol)"
                codigo_idioma="es"
            elif "(Latino)" in mirror_item.title:
                idioma="(Latino)"
                codigo_idioma="lat"
            elif "(VOS)" in mirror_item.title:
                idioma="(VOS)"
                codigo_idioma="vos"
            elif "(VO)" in mirror_item.title:
                idioma="(VO)"
                codigo_idioma="vo"
            else:
                idioma="(Desconocido)"
                codigo_idioma="desconocido"

            logger.info("pelisalacarta.platformcode.launcher filter_language=#"+filter_language+"#, codigo_idioma=#"+codigo_idioma+"#")
            if filter_language=="" or (filter_language!="" and filter_language==codigo_idioma):
                logger.info("pelisalacarta.platformcode.launcher download_all_episodes, downloading mirror")
            else:
                logger.info("pelisalacarta.platformcode.launcher language "+codigo_idioma+" filtered, skipping")
                continue

            if hasattr(channel, 'play'):
                video_items = channel.play(mirror_item)
            else:
                video_items = [mirror_item]

            if len(video_items)>0:
                video_item = video_items[0]

                # Comprueba que estÃ© disponible
                video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing( video_item.server , video_item.url , video_password="" , muestra_dialogo=False)

                # Lo aÃ±ade a la lista de descargas
                if puedes:
                    logger.info("pelisalacarta.platformcode.launcher download_all_episodes, downloading mirror started...")
                    # El vÃ­deo de mÃ¡s calidad es el Ãºltimo
                    mediaurl = video_urls[len(video_urls)-1][1]
                    devuelve = downloadtools.downloadbest(video_urls,show_title+" "+episode_title+" "+idioma+" ["+video_item.server+"]",continuar=False)

                    if devuelve==0:
                        logger.info("pelisalacarta.platformcode.launcher download_all_episodes, download ok")
                        descargado = True
                        break
                    elif devuelve==-1:
                        try:
                            import xbmcgui
                            advertencia = xbmcgui.Dialog()
                            resultado = advertencia.ok("plugin" , "Descarga abortada")
                        except:
                            pass
                        return
                    else:
                        logger.info("pelisalacarta.platformcode.launcher download_all_episodes, download error, try another mirror")
                        continue

                else:
                    logger.info("pelisalacarta.platformcode.launcher download_all_episodes, downloading mirror not available... trying next")

        if not descargado:
            logger.info("pelisalacarta.platformcode.launcher download_all_episodes, EPISODIO NO DESCARGADO "+episode_title)


def play_from_library(item, channel, server_white_list, server_black_list):
    logger.info("pelisalacarta.platformcode.launcher play_from_library")

    category = item.category
    fulltitle = item.show + " " + item.title

    logger.info("item.server=#"+item.server+"#")
    # Ejecuta find_videos, del canal o comÃºn
    try:
        itemlist = getattr(channel, "findvideos")(item)

        if config.get_setting('filter_servers') == 'true':
            itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

    except:
        from servers import servertools
        itemlist = servertools.find_video_items(item)

        if config.get_setting('filter_servers') == 'true':
            itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

    if len(itemlist) > 0:
        # for item2 in itemlist:
        #    logger.info(item2.title+" "+item2.subtitle)

        # El usuario elige el mirror
        opciones = []
        for item in itemlist:
            opciones.append(item.title)

        import xbmcgui
        dia = xbmcgui.Dialog()
        seleccion = dia.select(config.get_localized_string(30163), opciones)
        elegido = itemlist[seleccion]

        if seleccion == -1:
            return
    else:
        elegido = item

    # Ejecuta el mÃ©todo play del canal, si lo hay
    try:
        itemlist = channel.play(elegido)
        item = itemlist[0]
    except:
        item = elegido
    logger.info("Elegido %s (sub %s)" % (item.title, item.subtitle))

    from platformcode import xbmctools

    xbmctools.play_video(item, strmfile=True)
    logger.info("se espera 5 segundos por si falla al reproducir el fichero")
    import xbmc
    xbmc.sleep(5000)

    if xbmc.Player().isPlaying():
        from platformcode import library2 as library

        logger.info("pelisalacarta.platformcode.launcher play_from_library [{platform}]"
                    .format(platform=config.get_platform()))

        if library.is_compatible():
            # if config.get_platform() == "kodi-jarvis":
            # TODO crear variable en settings que diga si quieres marcar los episodios
            if 1 == 1:
                library.mark_as_watched(category)


def add_pelicula_to_library(item):
    logger.info("pelisalacarta.platformcode.launcher add_pelicula_to_library")
    from platformcode import library2 as library

    logger.info("pelisalacarta.platformcode.launcher add_pelicula_to_library [{platform}]"
                .format(platform=config.get_platform()))

    if library.is_compatible():
        # if config.get_platform() == "kodi-jarvis":
        new_item = item.clone(action="play_from_library", category="Cine")
        library.savelibrary(new_item)
    # retrocompatibilidad :)
    else:
        from platformcode import library
        # Obtiene el listado desde el que se llamÃ³
        library.savelibrary(titulo=item.fulltitle, url=item.url, thumbnail=item.thumbnail,
                            server=item.server, plot=item.plot, canal=item.channel, category="Cine",
                            Serie=item.show.strip(), verbose=False, accion="play_from_library",
                            pedirnombre=False, subtitle=item.subtitle)


def add_serie_to_library(item, channel):
    logger.info("pelisalacarta.platformcode.launcher add_serie_to_library, show=#"+item.show+"#")

    import xbmcgui

    # Obtiene el listado desde el que se llamÃ³
    action = item.extra

    itemlist = getattr(channel, action)(item)

    # TODO arreglar progress dialog
    # Progreso
    p_dialog = xbmcgui.DialogProgress()
    ret = p_dialog.create('pelisalacarta', 'AÃ±adiendo episodios...')
    p_dialog.update(0, 'AÃ±adiendo episodio...')
    totalepisodes = len(itemlist)

    logger.info("[launcher.py] Total Episodios:"+str(totalepisodes))
    i = 0
    errores = 0
    nuevos = 0
    for item in itemlist:
        logger.info("title:: {}".format(item.title))
        i += 1
        p_dialog.update(i*100/totalepisodes, 'AÃ±adiendo episodio...', item.title)
        logger.info("pelisalacarta.platformcode.launcher add_serie_to_library, title="+item.title)
        if p_dialog.iscanceled():
            return

        try:
            # AÃ±ade todos menos el que dice "AÃ±adir esta serie..." o "Descargar esta serie..."
            if item.action != "add_serie_to_library" and item.action != "download_all_episodes":

                from platformcode import library2 as library

                logger.info("pelisalacarta.platformcode.launcher add_serie_to_library [{platform}]"
                            .format(platform=config.get_platform()))
                if library.is_compatible():
                    # if config.get_platform() == "kodi-jarvis":
                    new_item = item.clone(action="play_from_library", category="Series")
                    nuevos = nuevos + library.savelibrary(new_item)

                # retrocompatibilidad :)
                else:
                    from platformcode import library
                    nuevos = nuevos + library.savelibrary(titulo=item.title, url=item.url, thumbnail=item.thumbnail,
                                                          server=item.server, plot=item.plot, canal=item.channel,
                                                          category="Series", Serie=item.show.strip(), verbose=False,
                                                          accion="play_from_library", pedirnombre=False,
                                                          subtitle=item.subtitle, extra=item.extra)
        except IOError:
            import sys
            for line in sys.exc_info():
                logger.error("%s" % line)
            logger.info("pelisalacarta.platformcode.launcherError al grabar el archivo "+item.title)
            errores += 1

    p_dialog.close()

    # Actualizacion de la biblioteca
    itemlist = []
    if errores > 0:
        itemlist.append(Item(title="ERROR, la serie NO se ha aÃ±adido a la biblioteca o lo ha hecho incompleta"))
        logger.info("[launcher.py] No se pudo aÃ±adir "+str(errores)+" episodios")
    else:
        itemlist.append(Item(title="La serie se ha aÃ±adido a la biblioteca"))
        logger.info("[launcher.py] NingÃºn error al aÃ±adir "+str(errores)+" episodios")

    # FIXME:jesus Comentado porque no funciona bien en todas las versiones de XBMC
    # library.update(totalepisodes,errores,nuevos)
    xbmctools.renderItems(itemlist, item)

    from platformcode import library2 as library

    if library.is_compatible():
        library.save_tvshow_in_file_xml(item)

    else:
        from platformcode import library

        # Lista con series para actualizar
        nombre_fichero_config_canal = os.path.join(config.get_library_path(), "series.xml")
        if not os.path.exists(nombre_fichero_config_canal):
            nombre_fichero_config_canal = os.path.join(config.get_data_path(), "series.xml")

        logger.info("nombre_fichero_config_canal="+nombre_fichero_config_canal)
        if not os.path.exists(nombre_fichero_config_canal):
            f = open(nombre_fichero_config_canal, "w")
        else:
            f = open(nombre_fichero_config_canal, "r")
            contenido = f.read()
            f.close()
            f = open(nombre_fichero_config_canal, "w")
            f.write(contenido)
        from platformcode import library
        f.write(library.title_to_folder_name(item.show)+","+item.url+","+item.channel+"\n")
        f.close()