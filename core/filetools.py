# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# filetools
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
# Gestion de archivos con discriminación samba/local

import locale
import os
import string
import sys
from socket import gaierror

from core import config
from core import logger
from platformcode import platformtools

try:
    from lib.sambatools import libsmb as samba

except ImportError:
    try:
        import xbmc
        librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
    except ImportError:
        xbmc = None
        librerias = os.path.join(config.get_runtime_path(), 'lib')

    sys.path.append(librerias)
    from sambatools import libsmb as samba


# TODO revisar con los caracteres validos dentro de title_to_filename()
def remove_chars(path):
    """
    Elimina cáracteres no permitidos
    @param path: cadena a validar
    @type path: str
    @rtype: str
    @return: devuelve la cadena sin los caracteres no permitidos
    """
    chars = ":*?<>|"
    if path.lower().startswith("smb://"):

        path = path[6:]
        return "smb://" + ''.join([c for c in path if c not in chars])

    else:
        if path.find(":\\") == 1:
            unidad = path[0:3]
            path = path[2:]
        else:
            unidad = ""

        return unidad + ''.join([c for c in path if c not in chars])


def encode(path, _samba=False):
    """
    Codifica una ruta segun el sistema operativo que estemos utilizando
    El argumento path tiene que estar codificado en UTF-8
    @type path str
    @param path parametro a codificar
    @type _samba bool
    @para _samba si la ruta es samba o no
    @rtype: str
    @return ruta encodeada
    """
    if path.lower().startswith("smb://") or _samba:
        path = unicode(path, "utf8")
    else:
        _ENCODING = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf-8'
        path = unicode(path, "utf8")
        path = path.encode(_ENCODING)

    return remove_chars(path)


def decode(path):
    """
    Descodifica una ruta segun el sistema operativo que estemos utilizando
    @param path: puede ser una ruta o un list() con varias rutas
    @rtype: str
    @return: ruta codificado en UTF-8
    """
    _ENCODING = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf-8'

    if type(path) == list:
        for x in range(len(path)):
            if not type(path[x]) == unicode:
                path[x] = path[x].decode(_ENCODING)
            path[x] = path[x].encode("utf8")
    else:
        if not type(path) == unicode:
            path = path.decode(_ENCODING)
        path = path.encode("utf8")
    return path


def read(path):
    """
    Lee el contenido de un archivo y devuelve los datos
    @param path: ruta del fichero
    @type path: str
    @rtype: str
    @return: datos que contiene el fichero
    """
    path = encode(path)
    data = ""
    if path.lower().startswith("smb://"):
        from sambatools.smb.smb_structs import OperationFailure
        try:
            with samba.get_file_handle_for_reading(os.path.basename(path), os.path.dirname(path)).read() as f:
                for line in f:
                    data += line
        except OperationFailure:
            logger.info("filetools.py read: ERROR al leer el archivo: {0}".format(path))

    else:
        try:
            with open(path, "rb") as f:
                for line in f:
                    data += line
        except EnvironmentError:
            logger.info("filetools.py read: ERROR al leer el archivo: {0}".format(path))

    return data


def write(path, data):
    """
    Guarda los datos en un archivo
    @param path: ruta del archivo a guardar
    @type path: str
    @param data: datos a guardar
    @type data: str
    @rtype: bool
    @return: devuelve True si se ha escrito correctamente o False si ha dado un error
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        from sambatools.smb.smb_structs import OperationFailure
        try:
            samba.store_file(os.path.basename(path), data, os.path.dirname(path))
        except OperationFailure:
            logger.info("filetools.py write: Error al guardar el archivo: {0}".format(path))
            return False
        else:
            return True

    else:
        try:
            with open(path, "wb") as f:
                f.write(data)
        except EnvironmentError:
            logger.info("filetools.py write: Error al guardar el archivo: {0}".format(path))
            return False
        else:
            return True


def open_for_reading(path):
    """
    Abre un archivo para leerlo
    @param path: ruta
    @type path: str
    @rtype: str
    @return: datos del fichero
    """
    path = encode(path)
    if path.lower().startswith("smb://"):

        return samba.get_file_handle_for_reading(os.path.basename(path), os.path.dirname(path))
    else:
        return open(path, "rb")


def rename(path, new_name):
    """
    Renombra un archivo o carpeta
    @param path: ruta del fichero o carpeta a renombrar
    @type path: str
    @param new_name: nuevo nombre
    @type new_name: str
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        new_name = encode(new_name, True)
        samba.rename(os.path.basename(path), new_name, os.path.dirname(path))
    else:
        new_name = encode(new_name, False)
        os.rename(path, os.path.join(os.path.dirname(path), new_name))


def exists(path):
    """
    Comprueba si existe una carpeta o fichero
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe, tanto si es una carpeta como un archivo
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        try:
            return samba.file_exists(os.path.basename(path), os.path.dirname(path)) or \
                   samba.folder_exists(os.path.basename(path), os.path.dirname(path))
        except gaierror:
            logger.info("filetools.py exists: No es posible conectar con la ruta")
            platformtools.dialog_notification("No es posible conectar con la ruta", path)
            return True
    else:
        return os.path.exists(path)


def isfile(path):
    """
    Comprueba si la ruta es un fichero
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe y es un archivo
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        return samba.file_exists(os.path.basename(path), os.path.dirname(path))
    else:
        return os.path.isfile(path)


def isdir(path):
    """
    Comprueba si la ruta es un directorio
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe y es un directorio
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        if path.endswith("/"):
            path = path[:-1]

        return samba.folder_exists(os.path.basename(path), os.path.dirname(path))
    else:
        return os.path.isdir(path)


def getsize(path):
    """
    Obtiene el tamaño de un archivo
    @param path: ruta del fichero
    @type path: str
    @rtype: str
    @return: tamaño del fichero
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        return samba.get_attributes(os.path.basename(path), os.path.dirname(path)).file_size
    else:
        return os.path.getsize(path)


def remove(path):
    """
    Elimina un archivo
    @param path: ruta del fichero a eliminar
    @type path: str
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        samba.delete_files(os.path.basename(path), os.path.dirname(path))
    else:
        os.remove(path)


def rmdir(path):
    """
    Elimina un directorio
    @param path: ruta a eliminar
    @type path: str
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        samba.delete_directory(os.path.basename(path), os.path.dirname(path))
    else:
        os.rmdir(path)


def mkdir(path):
    """
    Crea un directorio
    @param path: ruta a crear
    @type path: str
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        try:
            samba.create_directory(os.path.basename(path), os.path.dirname(path))
        except gaierror:
            logger.info("filetools.py mkdir: Error al crear la ruta")
            platformtools.dialog_notification("Error al crear la ruta", path)
    else:
        try:
            os.mkdir(path)
        except OSError:
            logger.info("filetools.py mkdir: Error al crear la ruta")
            platformtools.dialog_notification("Error al crear la ruta", path)


def join(*paths):
    """
    Junta varios directorios
    @rytpe: str
    @return: la ruta concatenada
    """
    if paths[0].lower().startswith("smb://"):
        return paths[0].strip("/") + "/" + "/".join(paths[1:])
    else:
        import os
        return os.path.join(*paths)


def walk(top, topdown=True, onerror=None):
    """
    Lista un directorio de manera recursiva
    @param top: Directorio a listar, debe ser un str "UTF-8"
    @type top: str
    @param topdown: se escanea de arriba a abajo
    @type topdown: bool
    @param onerror: muestra error para continuar con el listado si tiene algo seteado sino levanta una excepción
    @type onerror: bool
    ***El parametro followlinks que por defecto es True, no se usa aqui, ya que en samba no discrimina los links
    """
    top = encode(top)
    if top.lower().startswith("smb://"):
        try:
            names = listdir(top)
        except Exception, _err:
            if onerror is not None:
                onerror(_err)
            return

        dirs, nondirs = [], []
        for name in names:
            if isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)
        if topdown:
            yield top, dirs, nondirs

        for name in dirs:
            new_path = join(top, name)
            for x in walk(new_path, topdown, onerror):
                yield x
        if not topdown:
            yield top, dirs, nondirs

    else:
        for a, b, c in os.walk(top, topdown, onerror):
            # list(b) es para que haga una copia del listado de directorios
            # si no da error cuando tiene que entrar recursivamente en directorios con caracteres especiales
            yield decode(a), decode(list(b)), decode(c)


def listdir(path):
    """
    Lista un directorio
    @param path: Directorio a listar, debe ser un str "UTF-8"
    @type path: str
    @rtype: str
    @return: contenido de un directorio
    """

    path = encode(path)
    if path.lower().startswith("smb://"):
        files, directories = samba.get_files_and_directories(path)
        files_directories = files + directories
        return decode(files_directories)
    else:
        return decode(os.listdir(path))


def dirname(path):
    """
    Devuelve el directorio de una ruta
    @param path: ruta
    @type path: str
    @return: directorio de la ruta
    @rtype: str
    """
    # TODO pendiente parte samba
    _dir = os.path.dirname(path)

    return _dir


def elimina_tildes(s):
    """
    elimina las tildes de la cadena
    @type s: str
    @param s: cadena.
    @rtype:   str
    @return:  cadena sin tildes.
    """
    logger.info("filetools.py elimina_tildes")
    import unicodedata

    # TODO prueba para ver si se encodea correctamente en mac
    # if not isinstance(s, unicode):
    #     s = unicode(s)  # cast data to unicode
    #     return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

    if not isinstance(s, unicode):
        s = s.decode("UTF-8")
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    # s = s.replace("Á", "a")
    # s = s.replace("É", "e")
    # s = s.replace("Í", "i")
    # s = s.replace("Ó", "o")
    # s = s.replace("Ú", "u")
    # s = s.replace("á", "a")
    # s = s.replace("é", "e")
    # s = s.replace("í", "i")
    # s = s.replace("ó", "o")
    # s = s.replace("ú", "u")
    # s = s.replace("À", "a")
    # s = s.replace("È", "e")
    # s = s.replace("Ì", "i")
    # s = s.replace("Ò", "o")
    # s = s.replace("Ù", "u")
    # s = s.replace("à", "a")
    # s = s.replace("è", "e")
    # s = s.replace("ì", "i")
    # s = s.replace("ò", "o")
    # s = s.replace("ù", "u")
    # s = s.replace("ç", "c")
    # s = s.replace("Ç", "C")
    # s = s.replace("Ñ", "n")
    # s = s.replace("ñ", "n")

    # return s


def title_to_filename(title):
    """
    devuelve un titulo con caracteres válidos para crear un fichero
    @type title: str
    @param title: title.
    @rtype:   str
    @return:  cadena correcta sin tildes.
    """
    logger.info("filetools.py title_to_filename")
    logger.debug("title: " + title)
    
    title = remove_tags(title)
    
    safechars = string.letters + string.digits + " -_.[]()"
    folder_name = filter(lambda c: c in safechars, elimina_tildes(title))
    return str(folder_name)


def remove_tags(title):
    """
    devuelve el titulo sin tags como color
    @type title: str
    @param title: title
    @rtype: str
    @return: cadena sin tags
    """
    logger.info("filetools.py remove_tags")
    
    title_without_tags = scrapertools.find_single_match(title, '\[COLOR .+?\](.+)\[\/COLOR\]')
    
    if title_without_tags:
        return title_without_tags
    else:
        return title
