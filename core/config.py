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
# Parámetros de configuración (kodi)
# ------------------------------------------------------------

import os
import re

import xbmc
import xbmcaddon
import xbmcgui


PLUGIN_NAME = "pelisalaceppa"

__settings__ = xbmcaddon.Addon(id="plugin.video." + PLUGIN_NAME)
__language__ = __settings__.getLocalizedString


def get_platform(full_version=False):
    """
        Devuelve la información la version de xbmc o kodi sobre el que se ejecuta el plugin

        @param full_version: indica si queremos toda la informacion o no
        @type full_version: bool
        @rtype: str o dict
        @return: Si el paramentro full_version es True se retorna un diccionario con las siguientes claves:
            'num_version': (float) numero de version en formato XX.X
            'name_version': (str) nombre clave de cada version
            'video_db': (str) nombre del archivo que contiene la base de datos de videos
            'plaform': (str) esta compuesto por "kodi-" o "xbmc-" mas el nombre de la version segun corresponda.
        Si el parametro full_version es False (por defecto) se retorna el valor de la clave 'plaform' del diccionario anterior.
    """

    ret = {}
    codename = {"10": "dharma", "11": "eden", "12": "frodo",
                "13": "gotham", "14": "helix", "15": "isengard",
                "16": "jarvis", "17": "krypton", "18": "leia"}
    code_db = {'10': 'MyVideos37.db', '11': 'MyVideos60.db', '12': 'MyVideos75.db',
               '13': 'MyVideos78.db', '14': 'MyVideos90.db', '15': 'MyVideos93.db',
               '16': 'MyVideos99.db', '17': 'MyVideos107.db', '18': 'MyVideos108.db'}

    num_version = xbmc.getInfoLabel('System.BuildVersion')
    num_version = re.match("\d+\.\d+", num_version).group(0)
    ret['name_version'] = codename.get(num_version.split('.')[0], num_version)
    ret['video_db'] = code_db.get(num_version.split('.')[0], "")
    ret['num_version'] = float(num_version)
    if ret['num_version'] < 14:
        ret['platform'] = "xbmc-" + ret['name_version']
    else:
        ret['platform'] = "kodi-" + ret['name_version']

    if full_version:
        return ret
    else:
        return ret['platform']


def is_xbmc():
    return True


def get_library_support():
    return True


def get_system_platform():
    """ fonction: pour recuperer la platform que xbmc tourne """
    platform = "unknown"
    if xbmc.getCondVisibility("system.platform.linux"):
        platform = "linux"
    elif xbmc.getCondVisibility("system.platform.xbox"):
        platform = "xbox"
    elif xbmc.getCondVisibility("system.platform.windows"):
        platform = "windows"
    elif xbmc.getCondVisibility("system.platform.osx"):
        platform = "osx"
    return platform


def get_all_settings_addon():
    # Lee el archivo settings.xml y retorna un diccionario con {id: value}
    import scrapertools

    infile = open(os.path.join(get_data_path(), "settings.xml"), "r")
    data = infile.read()
    infile.close()

    ret = {}
    matches = scrapertools.find_multiple_matches(data, '<setting id="([^"]*)" value="([^"]*)')

    for _id, value in matches:
        ret[_id] = get_setting(_id)

    return ret


def open_settings():
    settings_pre = get_all_settings_addon()
    __settings__.openSettings()
    settings_post = get_all_settings_addon()

    # cb_validate_config (util para validar cambios realizados en el cuadro de dialogo)
    if settings_post.get('adult_aux_intro_password', None):
        # Hemos accedido a la seccion de Canales para adultos
        from platformcode import platformtools
        if 'adult_password' not in settings_pre:
            adult_password = set_setting('adult_password', '0000')
        else:
            adult_password = settings_pre['adult_password']

        if settings_post['adult_aux_intro_password'] == adult_password:
            # La contraseña de acceso es correcta

            # Cambio de contraseña
            if settings_post['adult_aux_new_password1']:
                if settings_post['adult_aux_new_password1'] == settings_post['adult_aux_new_password2']:
                    adult_password = set_setting('adult_password', settings_post['adult_aux_new_password1'])
                else:
                    platformtools.dialog_ok("Canales para adultos", "Los campos 'Nueva contraseña' y 'Confirmar nueva contraseña' no coinciden.",
                                            "Entre de nuevo en 'Preferencias' para cambiar la contraseña")

            # Fijar adult_pin
            adult_pin = ""
            if settings_post["adult_request_password"] == True:
                adult_pin = adult_password
            set_setting("adult_pin", adult_pin)

        else:
            platformtools.dialog_ok("Canales para adultos", "La contraseña no es correcta.",
                                    "Los cambios realizados en esta sección no se guardaran.")

            # Deshacer cambios
            set_setting("adult_mode", settings_pre.get("adult_mode", 0))
            set_setting("adult_request_password", settings_pre.get("adult_request_password", True))

        # Borramos settings auxiliares
        set_setting('adult_aux_intro_password', '')
        set_setting('adult_aux_new_password1', '')
        set_setting('adult_aux_new_password2', '')


def get_setting(name, channel="", server="", default=None):
    """
    Retorna el valor de configuracion del parametro solicitado.

    Devuelve el valor del parametro 'name' en la configuracion global, en la configuracion propia del canal 'channel' 
    o en la del servidor 'server'.

    Los parametros channel y server no deben usarse simultaneamente. Si se especifica el nombre del canal se devolvera 
    el resultado de llamar a channeltools.get_channel_setting(name, channel, default). Si se especifica el nombre del 
    servidor se devolvera el resultado de llamar a servertools.get_channel_setting(name, server, default). Si no se
    especifica ninguno de los anteriores se devolvera el valor del parametro en la configuracion global si existe o 
    el valor default en caso contrario.

    @param name: nombre del parametro
    @type name: str
    @param channel: nombre del canal
    @type channel: str
    @param server: nombre del servidor
    @type server: str
    @param default: valor devuelto en caso de que no exista el parametro name
    @type default: cualquiera

    @return: El valor del parametro 'name'
    @rtype: El tipo del valor del parametro 

    """

    # Specific channel setting
    if channel:
        # logger.info("config.get_setting reading channel setting '"+name+"' from channel xml")
        from core import channeltools
        value = channeltools.get_channel_setting(name, channel, default)
        # logger.info("config.get_setting -> '"+repr(value)+"'")
        return value

    # Specific server setting
    elif server:
        # logger.info("config.get_setting reading server setting '"+name+"' from server xml")
        from core import servertools
        value = servertools.get_server_setting(name, server, default)
        # logger.info("config.get_setting -> '"+repr(value)+"'")
        return value

    # Global setting
    else:
        # logger.info("config.get_setting reading main setting '"+name+"'")
        value = __settings__.getSetting(name)
        if not value:
            return default

        # Translate Path if start with "special://"
        if value.startswith("special://") and "librarypath" not in name:
            value = xbmc.translatePath(value)

        # hack para devolver el tipo correspondiente
        settings_types = get_settings_types()

        if settings_types.get(name) in ['enum', 'number']:
            try:
                value = int(value)
            except Exception, ex:
                from core import logger
                logger.error("Error al convertir '%s' de tipo 'enum','number' \n%s" % (value, ex))
                if value.lower() == "true":
                    # Fix temporal versiones <= 4.3
                    value = 1
                else:
                    value = 0

        elif settings_types.get(name) == 'bool':
            value = value == 'true'

        elif name not in settings_types:
            try:
                t = eval(value)
                value = t[0](t[1])
            except Exception, ex:
                from core import logger
                logger.error("Error al convertir '%s' se pasa como tipo 'None'\n%s" % (value, ex))
                value = None

        return value


def set_setting(name, value, channel="", server=""):
    """
    Fija el valor de configuracion del parametro indicado.

    Establece 'value' como el valor del parametro 'name' en la configuracion global o en la configuracion propia del
    canal 'channel'.
    Devuelve el valor cambiado o None si la asignacion no se ha podido completar.

    Si se especifica el nombre del canal busca en la ruta \addon_data\plugin.video.pelisalacarta\settings_channels el
    archivo channel_data.json y establece el parametro 'name' al valor indicado por 'value'. Si el archivo
    channel_data.json no existe busca en la carpeta channels el archivo channel.xml y crea un archivo channel_data.json
    antes de modificar el parametro 'name'.
    Si el parametro 'name' no existe lo añade, con su valor, al archivo correspondiente.


    Parametros:
    name -- nombre del parametro
    value -- valor del parametro
    channel [opcional] -- nombre del canal

    Retorna:
    'value' en caso de que se haya podido fijar el valor y None en caso contrario

    """
    if channel:
        from core import channeltools
        return channeltools.set_channel_setting(name, value, channel)
    elif server:
        from core import servertools
        return servertools.set_server_setting(name, value, server)
    else:
        try:
            settings_types = get_settings_types()

            if settings_types.get(name) == 'bool':
                if value:
                    new_value = "true"
                else:
                    new_value = "false"

            elif settings_types.get(name):
                new_value = str(value)

            else:
                if isinstance(value, basestring):
                    new_value = "(%s, %s)" % (type(value).__name__, repr(value))

                else:
                    new_value = "(%s, %s)" % (type(value).__name__, value)

            __settings__.setSetting(name, new_value)

        except Exception, ex:
            from core import logger
            logger.error("Error al convertir '%s' no se guarda el valor \n%s" % (value, ex))
            return None

        return value


def get_settings_types():
    """
    Devuelve un diccionario con los parametros (key) de la configuracion global y sus tipos (value)

    :return: dict 
    """
    WIN10000 = xbmcgui.Window(10000)
    settings_types = WIN10000.getProperty(PLUGIN_NAME + "_settings_types")

    if not settings_types:
        infile = open(os.path.join(get_runtime_path(), "resources", "settings.xml"))
        data = infile.read()
        infile.close()

        matches = re.findall('<setting id="([^"]*)" type="([^"]*)', data)
        settings_types = "{%s}" % ",".join("'%s': '%s'" % tup for tup in matches)

        WIN10000.setProperty(PLUGIN_NAME + "_settings_types", settings_types)

    return eval(settings_types)


def get_localized_string(code):
    dev = __language__(code)

    try:
        dev = dev.encode("utf-8")
    except:
        pass

    return dev


def get_library_config_path():
    value = get_setting("librarypath")
    if value == "":
        verify_directories_created()
        value = get_setting("librarypath")
    return value


def get_library_path():
    return xbmc.translatePath(get_library_config_path())


def get_temp_file(filename):
    return xbmc.translatePath(os.path.join("special://temp/", filename))


def get_runtime_path():
    return xbmc.translatePath(__settings__.getAddonInfo('Path'))


def get_data_path():
    dev = xbmc.translatePath(__settings__.getAddonInfo('Profile'))

    # Crea el directorio si no existe
    if not os.path.exists(dev):
        os.makedirs(dev)

    return dev


def get_cookie_data():
    import os
    ficherocookies = os.path.join(get_data_path(), 'cookies.dat')

    cookiedatafile = open(ficherocookies, 'r')
    cookiedata = cookiedatafile.read()
    cookiedatafile.close()

    return cookiedata


# Test if all the required directories are created
def verify_directories_created():
    from core import logger
    from core import filetools
    from platformcode import xbmc_library

    config_paths = [["librarypath",      "library"],
                    ["downloadpath",     "downloads"],
                    ["downloadlistpath", "downloads/list"],
                    ["settings_path",    "settings_channels"]]

    for path, default in config_paths:
        saved_path = get_setting(path)

        # Biblioteca
        if path == "librarypath":
            set_setting("library_version", "v4")
            if not saved_path:
                saved_path = xbmc_library.search_library_path()
                if saved_path:
                    set_setting(path, saved_path)

        if not saved_path:
            saved_path = "special://profile/addon_data/plugin.video." + PLUGIN_NAME + "/" + default
            set_setting(path, saved_path)

        if get_setting("library_set_content") == True and path in ["librarypath", "downloadpath"]:
            # logger.debug("library_set_content %s" % get_setting("library_set_content"))
            xbmc_library.add_sources(saved_path)

        saved_path = xbmc.translatePath(saved_path)
        if not filetools.exists(saved_path):
            logger.debug("Creating %s: %s" % (path, saved_path))
            filetools.mkdir(saved_path)

    config_paths = [["folder_movies", "CINE"],
                    ["folder_tvshows", "SERIES"]]

    for path, default in config_paths:
        saved_path = get_setting(path)

        if not saved_path:
            saved_path = default
            set_setting(path, saved_path)

        content_path = filetools.join(get_library_path(), saved_path)
        if not filetools.exists(content_path):
            logger.debug("Creating %s: %s" % (path, content_path))
            if filetools.mkdir(content_path) and get_setting("library_set_content") == True:
                xbmc_library.set_content(default)

        elif get_setting("library_ask_set_content") == 2:
            xbmc_library.set_content(default)

    try:
        from core import scrapertools
        # Buscamos el archivo addon.xml del skin activo
        skindir = filetools.join(xbmc.translatePath("special://home"), 'addons', xbmc.getSkinDir(),
                                 'addon.xml')
        # Extraemos el nombre de la carpeta de resolución por defecto
        folder = ""
        data = filetools.read(skindir)
        res = scrapertools.find_multiple_matches(data, '(<res .*?>)')
        for r in res:
            if 'default="true"' in r:
                folder = scrapertools.find_single_match(r, 'folder="([^"]+)"')
                break

        # Comprobamos si existe en pelisalacarta y sino es así, la creamos
        default = filetools.join(get_runtime_path(), 'resources', 'skins', 'Default')
        if folder and not filetools.exists(filetools.join(default, folder)):
            filetools.mkdir(filetools.join(default, folder))

        # Copiamos el archivo a dicha carpeta desde la de 720p si éste no existe o si el tamaño es diferente
        if folder and folder != '720p':
            for root, folders, files in filetools.walk(filetools.join(default, '720p')):
                for f in files:
                    if not filetools.exists(filetools.join(default, folder, f)) or \
                          (filetools.getsize(filetools.join(default, folder, f)) != 
                           filetools.getsize(filetools.join(default, '720p', f))):
                        filetools.copy(filetools.join(default, '720p', f),
                                       filetools.join(default, folder, f),
                                       True)
    except:
        import traceback
        logger.error("Al comprobar o crear la carpeta de resolución")
        logger.error(traceback.format_exc())
