# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# tvalacarta - XBMC Plugin
# ------------------------------------------------------------
# filter_tools
# se encarga de filtrar resultados
# ------------------------------------------------------------

import os
import string
import sys
import xbmc

from core import channeltools
from core import config
from core import logger
from core import jsontools
from core.item import Item


TAG_TVSHOWS = "TVSHOW_FILTER"
TAG_LANGUAGE = "language"
TAG_QUALITY_NOT_ALLOWED = "quality_not_allowed"


# TODO arreglar el filter para que haga el constructor con el json
class Filter:
    language = ""
    # quality = []
    quality_not_allowed = ""

    def __init__(self, dict_filter):
        self.language = dict_filter[TAG_LANGUAGE]
        self.quality_not_allowed = dict_filter[TAG_QUALITY_NOT_ALLOWED]


# todo mejorar tema de colores
# TODO mejorar logger
# todo echar un ojo a los .strip() y lower() que algunos son redundantes
# todo cuidado con el tema de los nombres raros de serie...
# todo documentar metodos
# todo meter try/catch
# todo echar un ojo a https://pyformat.info/, se puede formatear el estilo y hacer referencias directamente a elementos

# todo mirar
__channel__ = "filtertools"

# FILENAME = os.path.splitext(os.path.basename(__file__))[0]
DEBUG = config.get_setting("debug")

# try:
#     pluginhandle = int(sys.argv[1])
# except:
#     pluginhandle = ""


# hay que ponerlo sino da fallo en el launcher.py
def isGeneric():
    return True


def get_filtered_links(list_item):
    """
    Devuelve una lista de enlaces filtrados.

    :param list_item: lista de enlaces
    :type list_item: list[Item]
    :return: lista de Item
    :rtype: list[Item]
    """
    logger.info("[filtertools.py] get_filtered_links")

    if DEBUG:
        logger.info("total de items : {0}".format(len(list_item)))

    new_itemlist = []
    lista_aux = []
    quality_count = 0
    language_count = 0
    channel = list_item[0].channel
    has_filter = False
    filter = None

    dict_filtered_shows = get_filtered_shows(channel)
    if list_item[0].show.lower().strip() in dict_filtered_shows.keys():
        has_filter = True
        filter = Filter(dict_filtered_shows[list_item[0].show.lower().strip()])

    if has_filter:
        logger.info("filter datos: {0}".format(filter))

        for item in list_item:

            is_language_valid = True
            if filter.language != '':

                # viene de episodios
                if "[" in item.language:
                    if filter.language in item.language:
                        language_count += 1
                    else:
                        is_language_valid = False
                # viene de findvideos
                else:
                    if item.language.lower() == filter.language.lower():
                        language_count += 1
                    else:
                        is_language_valid = False

            is_quality_valid = True
            quality = ""

            # TODO mirar si hace falta quitar este if
            if filter.quality_not_allowed:
                # if DEBUG:
                #     logger.info("entra: calidad_no_permitida")
                if hasattr(item, 'quality'):
                    quality = item.quality.lower()
                    if item.quality.lower() not in filter.quality_not_allowed:
                        quality_count += 1
                    else:
                        is_quality_valid = False

            if is_language_valid and is_quality_valid:
                lista_aux.append(item)
                if DEBUG:
                    logger.info(" -Enlace añadido")

            if DEBUG:
                logger.info(" idioma valido?: {0}, item.language: {1}, filter.language: {2}"
                            .format(is_language_valid, item.language, filter.language))
                logger.info(" calidad valida?: {0}, item.quality: {1}, filter.quality_not_allowed: {2}"
                            .format(is_quality_valid, quality, filter.quality_not_allowed))

        for item in lista_aux:
            new_itemlist.append(Item(channel=channel, title=item.title, url=item.url, action=item.action,
                                     show=item.show, context=item.context))
            logger.info("{0} | context: {1}".format(item.title, item.context))
        # TODO mirar el context para cambiarlo por como dice super_berny

        logger.info("ITEMS FILTRADOS: {0}/{1}, idioma[{2}]:{3}, calidad_no_permitida{4}:{5}"
                    .format(len(new_itemlist), len(list_item), filter.language, language_count,
                            filter.quality_not_allowed, quality_count))

        if len(new_itemlist) == 0:
            # new_itemlist.append(Item(channel=__channel__, title="Obtener todos los servidores sin filtro",
            #                      url="", action="mainlist", show="kaka"))
            # new_itemlist = list_item
            # TODO CAMBIAR PARA QUE LLAME A GET_LINKS SIN FILTRO Y CAMBIAR CHANNEL Y ACTION??
            new_itemlist.append(Item(channel=channel, action="mainlist",
                                     title="[COLOR red]No se han encontrado items con el filtro [{0}] y ![{1}][/COLOR]"
                                     .format(filter.language, filter.quality_not_allowed), url="", thumbnail="",
                                     plot="", context="borrar filtro", show=list_item[0].show))
    else:
        new_itemlist = list_item

    return new_itemlist


def get_filtered_shows(from_channel):
    logger.info("[filtertools.py] get_filtered_shows")
    dict_series = {}
    name_file = from_channel
    # name_file = os.path.splitext(os.path.basename(__file__))[0]

    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))

    fname = os.path.join(config.get_data_path(), "settings_channels", name_file + "_data.json")

    data = read_file(fname)
    dict_data = jsontools.load_json(data)

    check_json_file(data, fname, dict_data)

    if TAG_TVSHOWS in dict_data:
        dict_series = dict_data[TAG_TVSHOWS]

        # TODO esto se deberia quitar, ya que se deberia guardar los keys con minusculas
        # ponemos en minusculas el key, ya que usamos el nombre de la serie como key.
        for key in dict_series.keys():
            new_key = key.lower()
            if new_key != key:
                dict_series[new_key] = dict_series[key]
                del dict_series[key]

    if DEBUG:
        logger.info("json_series: {0}".format(dict_series))

    return dict_series


def read_file(fname):
    """
    pythonic way to read from file
    :param: fname:
    :return: data
    :rtype: string
    """
    logger.info("[filtertools.py] read_file")
    data = ""

    if os.path.isfile(fname):
        try:
            with open(fname, "r") as f:
                for line in f:
                    data += line
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: {0}".format(fname))

    return data


def save_file(data, fname, message):
    """
    pythonic way to save data to file
    :param data:
    :param fname:
    :param message:
    :return:
    """
    logger.info("[filtertools.py] save_file")
    logger.info("default encoding: {0}".format(sys.getdefaultencoding()))
    try:
        with open(fname, "w") as f:
            try:
                f.write(data)
            except UnicodeEncodeError:
                logger.info("Error al realizar el encode, se usa uft8")
                f.write(data.encode('utf-8'))
    except EnvironmentError:
        message = "Error al guardar en disco"  # "[COLOR red]ERROR al guardar en disco,[/COLOR] "
    return message


def check_json_file(data, fname, dict_data):
    """
    Comprueba que si dict_data(conversion del fichero JSON a dict) no es un diccionario, se genere un fichero con
    data de nombre fname.bk.

    :param data: contenido del fichero fname
    :type data: str
    :param fname: nombre del fichero leido
    :type fname: str
    :param dict_data: nombre del diccionario
    :type dict_data: dict
    """
    logger.info("[filtertools.py] check_json_file")
    if not dict_data:
        logger.info("Error al cargar el json del fichero {0}".format(fname))

        if data != "":
            # se crea un nuevo fichero
            title = save_file(data, "{0}.bk".format(fname), "")
            if title != "":
                logger.info("Ha habido un error al guardar el fichero: {0}.bk"
                            .format(fname))
            else:
                logger.info("Se ha guardado una copia con el nombre: {0}.bk"
                            .format(fname))
        else:
            logger.info("Está vacío el fichero: {0}".format(fname))


def mainlist_filter(item):
    """
    Pantalla principal del filtro


    :param item:
    :return:
    """
    logger.info("[filtertools.py] mainlist_filter")
    itemlist = list([])
    dict_series = get_filtered_shows(item.from_channel)

    idx = 0
    for key in sorted(dict_series):
        tag_color = "green"
        if idx % 2 == 0:
            tag_color = "blue"
        idx += 1
        title = "Configurar [COLOR {0}][{1}][/COLOR]".format(tag_color, string.capwords(key))
        extra = "{0}##{1}##{2}".format(str(dict_series), key, str(dict_series[key]))

        itemlist.append(Item(channel=__channel__, action="config_filter", title=title, show=key, extra=extra,
                             from_channel=item.from_channel))

    return itemlist


def config_filter(item):
    logger.info("[filtertools.py] config_filter")
    logger.info("item {0}".format(item.tostring()))

    # OBTENEMOS LOS DATOS DEL channel.xml
    channel_xml = channeltools.get_channel_parameters(item.from_channel)
    list_calidad = channel_xml.get("list_quality", [])
    dict_idiomas = channel_xml.get("dict_tvshow_lang", {})
    logger.info("list-calidad {}".format(list_calidad))

    # OBTENEMOS LOS DATOS DEL JSON
    dict_series = get_filtered_shows(item.from_channel)
    # lang_selected = dict_idiomas["es"]
    # list_quality = ""

    lang_selected = dict_series.get(item.show.strip().lower(), {}).get(TAG_LANGUAGE, dict_idiomas.get("es", ""))
    list_quality = dict_series.get(item.show.strip().lower(), {}).get(TAG_QUALITY_NOT_ALLOWED, "")
    logger.info("lang selected {}".format(lang_selected))
    logger.info("list quality {}".format(list_quality))

    # if item.show.strip().lower() in dict_series.keys():
    #     if TAG_LANGUAGE in dict_series[item.show.strip().lower()].keys():
    #         lang_selected = dict_series[item.show.strip().lower()][TAG_LANGUAGE]
    #
    #     if TAG_QUALITY_NOT_ALLOWED in dict_series[item.show.strip().lower()].keys():
    #         list_quality = dict_series[item.show.strip().lower()][TAG_QUALITY_NOT_ALLOWED]

    list_idiomas = []
    for key in dict_idiomas.keys():
        list_idiomas.append(dict_idiomas[key])

    from platformcode import guitools
    list_controls = [{
            "id": "serie",
            "type": "label",
            "label": string.capwords(item.show.strip()),
            "default": "",  # En este caso: valor opcional que representa el color del texto
            "enabled": True,
            "visible": True,
            "lvalues": ""  # only for type = list
        },
        {
            "id": "language",
            "type": "list",   # bool, text, list, label
            "label": "Idioma",
            "default": lang_selected,
            "enabled": True,
            "visible": True,
            "lvalues": list_idiomas  # only for type = list
        }
    ]

    if list_calidad is not None:
        list_controls_calidad = [
            {
                "id": "textoCalidad",
                "type": "label",
                "label": "Calidad NO permitida",
                "default": "0xffC6C384",  # En este caso: valor opcional que representa el color del texto
                "enabled": True,
                "visible": True,
                "lvalues": ""  # only for type = list
            },
        ]
        for element in sorted(list_calidad, key=str.lower):
            list_controls_calidad.append({
                "id": element,
                "type": "bool",    # bool, text, list, label
                "label": element,
                "default": (0, 1)[element.lower() in list_quality],
                "enabled": True,
                "visible": True,
                "value": True,
                "lvalues": ""  # only for type = list
            })

        # concatenamos list_controls con list_controls_calidad
        list_controls.extend(list_controls_calidad)

    allow_delete = False
    if item.show.strip().lower() in dict_series:
        allow_delete = True

    list_controls_deleted_option = [
        {
            "id": "linea_blanco",
            "type": "label",
            "label": "",
            "default": "0xffC6C384",  # En este caso: valor opcional que representa el color del texto
            "enabled": allow_delete,
            "visible": allow_delete,
            "lvalues": ""  # only for type = list
        },
        {
            "id": "checkbox_deleted",
            "type": "bool",                       # bool, text, list, label
            "label": "¿Borrar filtro?",
            "default": False,
            "enabled": allow_delete,
            "visible": allow_delete,
            "lvalues": ""                         # only for type = list
        }
    ]
    list_controls.extend(list_controls_deleted_option)

    ventana = guitools.SettingWindow(list_controls=list_controls, caption="Filtrado de enlaces por Serie")
    ventana.doModal()

    if ventana.isConfirmed():
        logger.info("he pulsado en ok")

        dict_data_saved = dict(ventana.get_values())
        if dict_data_saved["checkbox_deleted"] != 1:
            logger.info("Se actualiza los datos")

            list_quality = []
            for key in dict_data_saved.keys():
                if list_calidad is not None:
                    if key in list_calidad:
                        if dict_data_saved[key] == 1:
                                list_quality.append(key.lower())

            dict_filter = {TAG_QUALITY_NOT_ALLOWED: list_quality, TAG_LANGUAGE: dict_data_saved[TAG_LANGUAGE]}
            dict_series[item.show.strip().lower()] = dict_filter

            message = "FILTRO GUARDADO"  # "[COLOR green]FILTRO GUARDADO,[/COLOR] "

        else:
            logger.info("borrado")
            dict_series.pop(item.show.strip().lower(), None)

            message = "FILTRO ELIMINADO"  # "[COLOR red]FILTRO ELIMINADO,[/COLOR] "

        fname, json_data = update_json_data(dict_series, item.from_channel)
        message = save_file(json_data, fname, message)

        xbmc.executebuiltin("Notification(\"{0}[{1}]\", \"{2}\")"
                            .format(string.capwords(item.show.strip()), dict_data_saved[TAG_LANGUAGE], message))
        xbmc.executebuiltin("XBMC.Action(back)")


def update_json_data(dict_series, name_file):
    """
    actualiza el json_data de un fichero con el diccionario pasado

    :param dict_series:
    :param name_file:
    :return:
    """
    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))
    fname = os.path.join(config.get_data_path(), "settings_channels", name_file + "_data.json")
    data = read_file(fname)
    dict_data = jsontools.load_json(data)
    # es un dict
    if dict_data:
        if TAG_TVSHOWS in dict_data:
            logger.info("   existe el key SERIES")
            dict_data[TAG_TVSHOWS] = dict_series
        else:
            logger.info("   NO existe el key SERIES")
            new_dict = {TAG_TVSHOWS: dict_series}
            dict_data.update(new_dict)
    else:
        logger.info("   NO es un dict")
        dict_data = {TAG_TVSHOWS: dict_series}
    json_data = jsontools.dump_json(dict_data)
    return fname, json_data


def save_filter(item):
    logger.info("[filtertools.py] save_filter")

    dict_series = get_filtered_shows(item.from_channel)

    name = item.show.strip().lower()  # string.capwords(item.show.strip())
    logger.info("[filtertools.py] config_filter name {0}".format(name))

    open_tag_idioma = (0, item.title.find("[")+1)[item.title.find("[") >= 0]
    close_tag_idioma = (0, item.title.find("]"))[item.title.find("]") >= 0]
    idioma = item.title[open_tag_idioma: close_tag_idioma]

    open_tag_calidad = (0, item.title.find("[", item.title.find("[") + 1)+1)[item.title.find("[", item.title.find("[") + 1) >= 0]
    close_tag_calidad = (0, item.title.find("]", item.title.find("]") + 1))[item.title.find("]", item.title.find("]") + 1) >= 0]
    calidad_no_permitida = ""  # item.title[open_tag_calidad: close_tag_calidad]

    # filter_idioma = ""
    # logger.info("idioma {0}".format(idioma))
    # if idioma != "":
    #     filter_idioma = [key for key, value in dict_idiomas.iteritems() if value == idioma][0]

    list_calidad = list([])

    dict_filter = {TAG_QUALITY_NOT_ALLOWED: list_calidad, TAG_LANGUAGE: idioma}
    dict_series[name] = dict_filter

    # filter_list = item.extra.split("##")
    # dict_series = eval(filter_list[0])
    # dict_filter = eval(filter_list[2])
    # dict_series[filter_list[1].strip().lower()] = dict_filter
    # logger.info("categoria {0}".format(item.from_channel))

    fname, json_data = update_json_data(dict_series, item.from_channel)

    message = "FILTRO GUARDADO"  # "[COLOR green]FILTRO GUARDADO,[/COLOR] "
    message = save_file(json_data, fname, message)

    xbmc.executebuiltin("Notification(\"{0}[{1}]\", \"{2}\")".format(string.capwords(item.show.strip()), idioma, message))
    xbmc.executebuiltin("XBMC.Action(back)")


def del_filter(item):
    logger.info("[filtertools.py] del_filter")

    dict_series = get_filtered_shows(item.from_channel)

    key = item.show.strip().lower()
    message = "FILTRO Borrado"  # "[COLOR green]FILTRO Borrado,[/COLOR] "
    try:
        del dict_series[key]

        fname, json_data = update_json_data(dict_series, item.from_channel)
        message = save_file(json_data, fname, message)

    except KeyError:
        message = "ERROR al borrar el filtro"  # "[COLOR red]ERROR al borrar el filtro,[/COLOR] "

    xbmc.executebuiltin("Notification(\"{0}\", \"{1}\")".format(string.capwords(item.show.strip()), message))
    xbmc.executebuiltin("XBMC.Action(back)")
