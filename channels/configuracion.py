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
# Configuracion
# ------------------------------------------------------------

from core import config
from core.item import Item
from core import logger
from core import filetools

DEBUG = True
CHANNELNAME = "configuracion"


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=CHANNELNAME, title="Preferencias", action="settings", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="", action="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))

    itemlist.append(Item(channel=CHANNELNAME, title="Ajustes especiales", action="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel="novedades", title="   Ajustes de la sección 'Novedades'", action="menu_opciones",
                         folder=True, thumbnail=get_thumbnail_path("thumb_novedades.png")))
    itemlist.append(Item(channel="buscador", title="   Ajustes del buscador global", action="opciones", folder=True,
                         thumbnail=get_thumbnail_path("thumb_buscar.png")))

    if config.get_library_support():
        itemlist.append(Item(channel="biblioteca", title="   Ajustes de la biblioteca",
                             action="channel_config", folder=True,
                             thumbnail=get_thumbnail_path("thumb_biblioteca.png")))
        itemlist.append(Item(channel="biblioteca", action="update_biblio", folder=False,
                             thumbnail=get_thumbnail_path("thumb_biblioteca.png"),
                             title="   Buscar nuevos episodios y actualizar biblioteca"))
    itemlist.append(Item(channel=CHANNELNAME, title="   Herramientas", action="submenu_tools",
                         folder=True, thumbnail=get_thumbnail_path("thumb_configuracion.png")))

    itemlist.append(Item(channel=CHANNELNAME, title="   Comprobar actualizaciones", action="check_for_updates",
                         folder=False, thumbnail=get_thumbnail_path("Crystal_Clear_action_info.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="   Añadir o Actualizar canal/conector desde una URL",
                         action="menu_addchannels"))
    itemlist.append(Item(channel=item.channel, action="", title="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))

    itemlist.append(Item(channel=CHANNELNAME, title="Ajustes por canales", action="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))

    import channelselector
    from core import channeltools
    channel_list = channelselector.filterchannels("all")

    for channel in channel_list:
        jsonchannel = channeltools.get_channel_json(channel.channel)
        if jsonchannel.get("settings"):
            setting = jsonchannel["settings"]
            if type(setting) == list:
                if len([s for s in setting if "id" in s and "include_in_" not in s["id"]]):
                    itemlist.append(Item(channel=CHANNELNAME,  title="   Configuración del canal '%s'" % channel.title,
                                         action="channel_config", config=channel.channel, folder=False,
                                         thumbnail=channel.thumbnail))

    return itemlist


def channel_config(item):
    from platformcode import platformtools
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "channels",
                                                                          item.config))


def check_for_updates(item):
    from core import updater

    try:
        version = updater.checkforupdates()
        if version:
            from platformcode import platformtools
            yes_pressed = platformtools.dialog_yesno("Versión "+version+" disponible", "¿Quieres instalarla?")

            if yes_pressed:
                item = Item(version=version)
                updater.update(item)

    except:
        pass


def settings(item):
    config.open_settings()


def menu_addchannels(item):
    logger.info()
    itemlist = list()
    itemlist.append(Item(channel=CHANNELNAME, title="# Copia de seguridad automática en caso de sobrescritura",
                         action="", text_color="green"))
    itemlist.append(Item(channel=CHANNELNAME, title="Añadir o actualizar canal", action="addchannel", folder=False))
    itemlist.append(Item(channel=CHANNELNAME, title="Añadir o actualizar conector", action="addchannel", folder=False))
    itemlist.append(Item(channel=CHANNELNAME, title="Mostrar ruta de carpeta para copias de seguridad",
                         action="backups", folder=False))
    itemlist.append(Item(channel=CHANNELNAME, title="Eliminar copias de seguridad guardadas", action="backups",
                         folder=False))

    return itemlist


def addchannel(item):
    from platformcode import platformtools
    import os
    import time
    logger.info()

    tecleado = platformtools.dialog_input("", "Introduzca la URL")
    if not tecleado:
        return
    logger.info("url=%s" % tecleado)

    local_folder = config.get_runtime_path()
    if "canal" in item.title:
        local_folder = filetools.join(local_folder, 'channels')
        folder_to_extract = "channels"
        info_accion = "canal"
    else:
        local_folder = filetools.join(local_folder, 'servers')
        folder_to_extract = "servers"
        info_accion = "conector"

    # Detecta si es un enlace a un .py o .xml (pensado sobre todo para enlaces de github)
    try:
        extension = tecleado.rsplit(".", 1)[1]
    except:
        extension = ""

    files = []
    zip = False
    if extension == "py" or extension == "xml":
        filename = tecleado.rsplit("/", 1)[1]
        localfilename = filetools.join(local_folder, filename)
        files.append([tecleado, localfilename, filename])
    else:
        import re
        from core import scrapertools
        # Comprueba si la url apunta a una carpeta completa (channels o servers) de github
        if re.search(r'https://github.com/[^\s]+/'+folder_to_extract, tecleado):
            try:
                data = scrapertools.downloadpage(tecleado)
                matches = scrapertools.find_multiple_matches(data,
                                                             '<td class="content">.*?href="([^"]+)".*?title="([^"]+)"')
                for url, filename in matches:
                    url = "https://raw.githubusercontent.com" + url.replace("/blob/", "/")
                    localfilename = filetools.join(local_folder, filename)
                    files.append([url, localfilename, filename])
            except:
                import traceback
                logger.info("Detalle del error: %s" % traceback.format_exc())
                platformtools.dialog_ok("Error", "La url no es correcta o no está disponible")
                return
        else:
            filename = 'new%s.zip' % info_accion
            localfilename = filetools.join(config.get_data_path(), filename)
            files.append([tecleado, localfilename, filename])
            zip = True

    logger.info("localfilename=%s" % localfilename)
    logger.info("descarga fichero...")

    try:
        if len(files) > 1:
            lista_opciones = ["No", "Sí", "Sí (Sobrescribir todos)"]
            overwrite_all = False
        from core import downloadtools
        for url, localfilename, filename in files:
            result = downloadtools.downloadfile(url, localfilename, continuar=False)
            if result == -3:
                if len(files) == 1:
                    dyesno = platformtools.dialog_yesno("El archivo ya existe", "Ya existe el %s %s. "
                                                                                "¿Desea sobrescribirlo?" %
                                                        (info_accion, filename))
                else:
                    if not overwrite_all:
                        dyesno = platformtools.dialog_select("El archivo %s ya existe, ¿desea sobrescribirlo?"
                                                             % filename, lista_opciones)
                    else:
                        dyesno = 1
                # Diálogo cancelado
                if dyesno == -1:
                    return
                # Caso de carpeta github, opción sobrescribir todos
                elif dyesno == 2:
                    overwrite_all = True
                elif dyesno:
                    hora_folder = "Copia seguridad [%s]" % time.strftime("%d-%m_%H-%M", time.localtime())
                    backup = filetools.join(config.get_data_path(), 'backups', hora_folder, folder_to_extract)
                    if not filetools.exists(backup):
                        os.makedirs(backup)
                    import shutil
                    shutil.copy2(localfilename, filetools.join(backup, filename))
                    downloadtools.downloadfile(url, localfilename, continuar=True)
                else:
                    if len(files) == 1:
                        return
                    else:
                        continue
    except:
        import traceback
        logger.info("Detalle del error: %s" % traceback.format_exc())
        return

    if zip:
        try:
            # Lo descomprime
            logger.info("descomprime fichero...")
            from core import ziptools
            unzipper = ziptools.ziptools()
            logger.info("destpathname=%s" % local_folder)
            unzipper.extract(localfilename, local_folder, folder_to_extract, True, True)
        except:
            import traceback
            logger.error("Detalle del error: %s" % traceback.format_exc())
            # Borra el zip descargado
            filetools.remove(localfilename)
            platformtools.dialog_ok("Error", "Se ha producido un error extrayendo el archivo")
            return

        # Borra el zip descargado
        logger.info("borra fichero...")
        filetools.remove(localfilename)
        logger.info("...fichero borrado")

    platformtools.dialog_ok("Éxito", "Actualización/Instalación realizada correctamente")


def backups(item):
    from platformcode import platformtools
    logger.info()

    ruta = filetools.join(config.get_data_path(), 'backups')
    ruta_split = ""
    if "ruta" in item.title:
        heading = "Ruta de copias de seguridad"
        if not filetools.exists(ruta):
            folders = "Carpeta no creada"
        else:
            folders = str(len(filetools.listdir(ruta))) + " copia/s de seguridad guardadas"
        if len(ruta) > 55:
            ruta_split = ruta[55:]
            ruta = ruta[:55]
        platformtools.dialog_ok(heading, ruta, ruta_split, folders)
    else:
        if not filetools.exists(ruta):
            platformtools.dialog_ok("La carpeta no existe", "No hay copias de seguridad guardadas")
        else:
            dyesno = platformtools.dialog_yesno("Las copias de seguridad se eliminarán", "¿Está seguro?")
            if dyesno:
                import shutil
                shutil.rmtree(ruta, ignore_errors=True)


def get_thumbnail_path(thumb_name):
    import urlparse
    web_path = "http://media.tvalacarta.info/pelisalacarta/squares/"
    return urlparse.urljoin(web_path, thumb_name)


def submenu_tools(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=CHANNELNAME, title="Canales", action="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="   Activar/Desactivar canales",
                         action="conf_tools", folder=True, extra="channels_onoff",
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel=CHANNELNAME,
                         title="   [COLOR red]Para solucion de errores[/COLOR]",
                         action="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="      Comprobar archivos *_data.json",
                         action="conf_tools", folder=True, extra="lib_check_datajson",
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="Libreria", action="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel=CHANNELNAME,
                         title="   [COLOR red]Para solucion de errores[/COLOR]",
                         action="", folder=False,
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))
    itemlist.append(Item(channel=CHANNELNAME,
                         title="      Comprobar archivos tvshow.nfo",
                         action="conf_tools", folder=True, extra="lib_check_tvshownfo",
                         thumbnail=get_thumbnail_path("thumb_configuracion.png")))

    return itemlist


def conf_tools(item):
    logger.info()
    itemlist = []

    # Activar/Desactivar canales
    if item.extra == "channels_onoff":
        import channelselector
        from core import channeltools
        channel_list = channelselector.filterchannels("allchannelstatus")
        excluded_channels = ['tengourl',
                             'buscador',
                             'libreria',
                             'configuracion',
                             'novedades',
                             'personal',
                             'ayuda']
        itemlist.append(Item(channel=CHANNELNAME, title="Modificar todos los canales",
                             action="channel_status", folder=False,
                             thumbnail=get_thumbnail_path("thumb_configuracion.png"),
                             extra="onoffall"))

        for channel in channel_list:
            try:
                # Si el canal esta en la lista de exclusiones lo saltamos
                if channel.channel not in excluded_channels:
                    # Se cargan los ajustes del archivo json del canal
                    jsonchannel = channeltools.get_channel_json(channel.channel)
                    if jsonchannel.get("settings") or jsonchannel.get("active"):
                        channel_parameters = channeltools.get_channel_parameters(channel.channel)
                        xml_status = None
                        status = None
                        xml_status = channel_parameters["active"]
                        xmlwasfalse = "false"
                        if config.get_setting("enabled", channel.channel):
                            status = config.get_setting("enabled", channel.channel)
                            # logger.info(channel.channel + " | Status: " + status)
                        else:
                            status = xml_status
                            # logger.info(channel.channel + " | Status (XML): " + status)
                        # Si en el xml estaba desactivado puede ser por algo
                        if xml_status == "false":
                            xmlwasfalse = "true"

                        # Si se ha establecido el estado del canal se añade a la lista
                        if status is not None:
                            list_status = None
                            if xmlwasfalse == "true":
                                if status == "true":
                                    list_status = " - [COLOR green]ACTIVADO[/COLOR] [COLOR red](DESACTIVADO POR DEFECTO)[/COLOR]"
                                if status == "false":
                                    list_status = " - [COLOR red]DESACTIVADO[/COLOR]"
                            else:
                                if status == "true":
                                    list_status = " - [COLOR green]ACTIVADO[/COLOR]"
                                if status == "false":
                                    list_status = " - [COLOR red]DESACTIVADO[/COLOR] [COLOR green](ACTIVADO POR DEFECTO)[/COLOR]"

                            if list_status is not None:
                                itemlist.append(Item(channel=CHANNELNAME,
                                                     title=channel.title + list_status,
                                                     action="channel_status", folder=False,
                                                     thumbnail=channel.thumbnail,
                                                     extra=channel.channel))
                    else:
                        logger.info("Algo va mal con el canal " + channel.channel)
                else:
                    continue
            except:
                import traceback
                from platformcode import platformtools
                logger.info(channel.title + " | Detalle del error: %s" % traceback.format_exc())
                platformtools.dialog_notification("Error",
                                                  "Se ha producido un error con el canal" +
                                                  channel.title)

    # Comprobacion de archivos channel_data.json
    elif item.extra == "lib_check_datajson":
        import channelselector
        from core import channeltools
        channel_list = channelselector.filterchannels("allchannelstatus")

        # Tener una lista de exclusion no tiene mucho sentido por que se comprueba si
        # el xml tiene "settings", pero por si acaso se deja
        excluded_channels = ['tengourl',
                             'configuracion',
                             'personal',
                             'ayuda']

        for channel in channel_list:
            try:
                import os
                from core import jsontools

                needsfix = None
                list_status = None
                list_controls = None
                default_settings = None
                channeljson_exists = None

                # Se convierte el "channel.channel" del canal biblioteca para que no de error
                if channel.channel == "libreria":
                    channel.channel = "biblioteca"

                # Se comprueba si el canal esta en la lista de exclusiones
                if channel.channel not in excluded_channels:
                    # Se comprueba que tenga "settings", sino se salta
                    jsonchannel = channeltools.get_channel_json(channel.channel)
                    if not jsonchannel.get("settings"):
                        itemlist.append(Item(channel=CHANNELNAME,
                                             title=channel.title + " - No tiene ajustes por defecto",
                                             action="", folder=False,
                                             thumbnail=channel.thumbnail))
                        continue
                        # logger.info(channel.channel + " SALTADO!")

                    # Se cargan los ajustes del archivo json del canal
                    file_settings = os.path.join(config.get_data_path(), "settings_channels",
                                                 channel.channel + "_data.json")
                    dict_settings = {}
                    dict_file = {}
                    if filetools.exists(file_settings):
                        # logger.info(channel.channel + " Tiene archivo _data.json")
                        channeljson_exists = "true"
                        # Obtenemos configuracion guardada de ../settings/channel_data.json
                        try:
                            dict_file = jsontools.load_json(open(file_settings, "rb").read())
                            if isinstance(dict_file, dict) and 'settings' in dict_file:
                                dict_settings = dict_file['settings']
                        except EnvironmentError:
                            logger.info("ERROR al leer el archivo: {0}".format(file_settings))
                    else:
                        # logger.info(channel.channel + " No tiene archivo _data.json")
                        channeljson_exists = "false"

                    if channeljson_exists == "true":
                        try:
                            datajson_size = filetools.getsize(file_settings)
                        except:
                            import traceback
                            logger.info(channel.title +
                                        " | Detalle del error: %s" % traceback.format_exc())
                    else:
                        datajson_size = None

                    # Si el _data.json esta vacio o no existe...
                    if (len(dict_settings) and datajson_size) == 0 or channeljson_exists == "false":
                        # Obtenemos controles del archivo ../channels/channel.xml
                        needsfix = "true"
                        try:
                            # Se cargan los ajustes por defecto
                            list_controls, default_settings = channeltools.get_channel_controls_settings(channel.channel)
                            # logger.info(channel.title + " | Default: %s" % default_settings)
                        except:
                            import traceback
                            logger.info(channel.title + " | Detalle del error: %s" % traceback.format_exc())
                            # default_settings = {}

                        # Si _data.json necesita ser reparado o no existe...
                        if needsfix == "true" or channeljson_exists == "false":
                            if default_settings is not None:
                                # Creamos el channel_data.json
                                default_settings.update(dict_settings)
                                dict_settings = default_settings
                                dict_file['settings'] = dict_settings
                                # Creamos el archivo ../settings/channel_data.json
                                json_data = jsontools.dump_json(dict_file)
                                try:
                                    open(file_settings, "wb").write(json_data)
                                    # logger.info(channel.channel + " - Archivo _data.json GUARDADO!")
                                    # El channel_data.json se ha creado/modificado
                                    list_status = " - [COLOR red] CORREGIDO!![/COLOR]"
                                except EnvironmentError:
                                    logger.info("ERROR al salvar el archivo: {0}".format(file_settings))
                            else:
                                if default_settings is None:
                                    list_status = " - [COLOR red] Imposible cargar los ajustes por defecto![/COLOR]"

                    else:
                        # logger.info(channel.channel + " - NO necesita correccion!")
                        needsfix = "false"

                    # Si se ha establecido el estado del canal se añade a la lista
                    if needsfix is not None:
                        if needsfix == "true":
                            if channeljson_exists == "false":
                                list_status = " - [COLOR red] Ajustes creados!![/COLOR]"
                            else:
                                list_status = " - [COLOR green] No necesita correccion[/COLOR]"
                        else:
                            # Si "needsfix" es "false" y "datjson_size" es None habra
                            # ocurrido algun error
                            if datajson_size is None:
                                list_status = " - [COLOR red] Ha ocurrido algun error[/COLOR]"
                            else:
                                list_status = " - [COLOR green] No necesita correccion[/COLOR]"

                    if list_status is not None:
                        itemlist.append(Item(channel=CHANNELNAME,
                                             title=channel.title + list_status,
                                             action="", folder=False,
                                             thumbnail=channel.thumbnail))
                    else:
                        logger.info("Algo va mal con el canal " + channel.channel)

                # Si el canal esta en la lista de exclusiones lo saltamos
                else:
                    continue
            except:
                import traceback
                from platformcode import platformtools
                logger.info(channel.title + " | Detalle del error: %s" % traceback.format_exc())
                platformtools.dialog_notification("Error",
                                                  "Se ha producido un error con el canal" +
                                                  channel.title)

    # Comprobacion de archivos "tvshow.nfo" de la libreria
    # Actuamente solo comprueba los parametros 'action' y 'get_temporadas' y los modifica
    elif item.extra == "lib_check_tvshownfo":
        try:
            from core import library
            for raiz, subcarpetas, ficheros in filetools.walk(library.TVSHOWS_PATH):
                for f in ficheros:
                    if f == "tvshow.nfo":
                        tvshow_path = filetools.join(raiz, f)
                        # logger.debug(tvshow_path)
                        head_nfo, item_tvshow = library.read_nfo(tvshow_path)

                        tvshow_title = None
                        nfo_error = None
                        old_action = None
                        new_action = None
                        new_channel = None
                        old_channel = None
                        if item_tvshow.channel != "biblioteca":
                            nfo_error = "channel"
                            old_channel = " - OLD 'channel': " + item_tvshow.channel
                            new_channel = " - NEW 'channel': biblioteca"
                            item_tvshow.channel = "biblioteca"
                        if item_tvshow.action != "get_temporadas":
                            nfo_error = "action"
                            old_action = " - OLD 'action': " + item_tvshow.action
                            new_action = " - NEW 'action': get_temporadas"
                            item_tvshow.action = "get_temporadas"

                        tvshow_title = item_tvshow.title

                        if nfo_error is not None:
                            filetools.write(tvshow_path, head_nfo + item_tvshow.tojson())
                            itemlist.append(Item(channel=CHANNELNAME,
                                                 title=tvshow_title + " - [COLOR red]CORREGIDO![/COLOR]",
                                                 action="", folder=False))
                            if old_action is not None:
                                itemlist.append(Item(channel=CHANNELNAME,
                                                     title="    " + tvshow_title + old_action,
                                                     action="", folder=False))
                                itemlist.append(Item(channel=CHANNELNAME,
                                                     title="    " + tvshow_title + new_action,
                                                     action="", folder=False))
                            if old_channel is not None:
                                itemlist.append(Item(channel=CHANNELNAME,
                                                     title="    " + tvshow_title + old_channel,
                                                     action="", folder=False))
                                itemlist.append(Item(channel=CHANNELNAME,
                                                     title="    " + tvshow_title + new_channel,
                                                     action="", folder=False))
                        else:
                            itemlist.append(Item(channel=CHANNELNAME,
                                            title=tvshow_title + " - [COLOR green]CORRECTO![/COLOR]",
                                            action="", folder=False))
                # logger.info("Creando tvshow.nfo: " + tvshow_path)
        except:
            import traceback
            from platformcode import platformtools
            logger.info("Detalle del error: %s" % traceback.format_exc())
            platformtools.dialog_notification("Error", "Se ha producido un error!")

    else:
        from platformcode import platformtools
        platformtools.dialog_notification("pelisalacarta", "Error!")
        platformtools.itemlist_update(Item(channel=CHANNELNAME, action="submenu_tools"))

    return itemlist


def channel_status(item):
    try:
        from platformcode import platformtools
        from core import channeltools

        if item.extra == "onoffall":
            # Opciones para el dialogo
            op_all = ["Activar todos", "Desactivar todos", "Recuperar estado por defecto de todos"]
            # Mostramos el dialogo
            seleccion_all = platformtools.dialog_select("Todos los canales - Elige una opción", op_all)
            # -1 es cancelar
            if seleccion_all == -1:
                return

            # logger.info("opcion numero = " + str(seleccion_all))
            import channelselector
            channel_list = channelselector.filterchannels("allchannelstatus")
            excluded_channels = ['tengourl',
                                 'buscador',
                                 'libreria',
                                 'configuracion',
                                 'novedades',
                                 'personal',
                                 'ayuda']
            for channel in channel_list:
                if channel.channel not in excluded_channels:
                    channel_parameters = channeltools.get_channel_parameters(channel.channel)
                    new_status_all_default = None
                    new_status_all = None
                    new_status_all_default = channel_parameters["active"]
                    # Opcion Activar todos
                    if seleccion_all == 0:
                        new_status_all = "true"
                    # Opcion Desactivar todos
                    if seleccion_all == 1:
                        new_status_all = "false"
                    # Opcion Recuperar estado por defecto
                    if seleccion_all == 2:
                        # Si tiene "enabled" en el json es porque el estado no es el del xml
                        if config.get_setting("enabled", channel.channel):
                            new_status_all = new_status_all_default

                        # Si el canal no tiene "enabled" en el json no se guarda, se pasa al siguiente
                        else:
                            continue

                    # Se guarda el estado del canal
                    if new_status_all is not None:
                        config.set_setting("enabled", new_status_all, channel.channel)

                else:
                    continue

            platformtools.dialog_notification("pelisalacarta", "Todos los canales - Ajuste guardado")
            platformtools.itemlist_update(Item(channel=CHANNELNAME, action="conf_tools",
                                               extra="channels_onoff"))

        else:
            # Opciones para el dialogo
            opciones = ["Activar", "Desactivar", "Por defecto"]
            # Mostramos el dialogo
            seleccion = platformtools.dialog_select(item.extra + " - Elige una opcion", opciones)
            # -1 es cancelar
            if seleccion == -1:
                return

            # logger.info("opcion numero = " + str(seleccion))
            new_status = None
            channel_parameters = channeltools.get_channel_parameters(item.extra)
            new_status_default = channel_parameters["active"]
            # Opcion Activar
            if seleccion == 0:
                new_status = "true"
            # Opcion Desactivar
            if seleccion == 1:
                new_status = "false"
            # Opcion Por defecto
            if seleccion == 2:
                new_status = new_status_default

            if new_status is not None:
                config.set_setting("enabled", new_status, item.extra)
                logger.info("Ajuste del canal " + item.extra + " guardado!")
            else:
                logger.info("Ajuste del canal " + item.extra + " NO guardado!")

            platformtools.dialog_notification("pelisalacarta", item.extra + " - Ajuste guardado")
            platformtools.itemlist_update(Item(channel=CHANNELNAME, action="conf_tools",
                                               extra="channels_onoff"))

    except:
        import traceback
        from platformcode import platformtools
        logger.info("Detalle del error: %s" % traceback.format_exc())
        platformtools.dialog_notification("Error",
                                          "Se ha producido un error al guardar")
