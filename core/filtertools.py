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

from core import config
from core import jsontools
from core import logger
from core.item import Item
from platformcode import platformtools

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

DEBUG = config.get_setting("debug")


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
    quality_count = 0
    language_count = 0
    channel = list_item[0].channel
    _filter = None

    dict_filtered_shows = get_filtered_tvshows(channel)
    if list_item[0].show.lower().strip() in dict_filtered_shows.keys():
        _filter = Filter(dict_filtered_shows[list_item[0].show.lower().strip()])

    if _filter:
        logger.info("filter datos: {0}".format(_filter))

        for item in list_item:

            is_language_valid = True
            if _filter.language:

                # viene de episodios
                if "[" in item.language:
                    if _filter.language in item.language:
                        language_count += 1
                    else:
                        is_language_valid = False
                # viene de findvideos
                else:
                    if item.language.lower() == _filter.language.lower():
                        language_count += 1
                    else:
                        is_language_valid = False

            is_quality_valid = True
            quality = ""

            # TODO mirar si hace falta quitar este if
            if _filter.quality_not_allowed:
                # if DEBUG:
                #     logger.info("entra: calidad_no_permitida")
                if hasattr(item, 'quality'):
                    #quality = item.quality.lower()
                    if item.quality.lower() not in _filter.quality_not_allowed:
                        quality_count += 1
                    else:
                        is_quality_valid = False

            if is_language_valid and is_quality_valid:
                new_item = item.clone(channel=channel)
                new_itemlist.append(new_item)
                logger.info("{0} | context: {1}".format(item.title, item.context))
                # TODO mirar el context para cambiarlo por como dice super_berny
                if DEBUG:
                    logger.info(" -Enlace añadido")

            if DEBUG:
                logger.info(" idioma valido?: {0}, item.language: {1}, filter.language: {2}"
                            .format(is_language_valid, item.language, _filter.language))
                logger.info(" calidad valida?: {0}, item.quality: {1}, filter.quality_not_allowed: {2}"
                            .format(is_quality_valid, quality, _filter.quality_not_allowed))

        logger.info("ITEMS FILTRADOS: {0}/{1}, idioma[{2}]:{3}, calidad_no_permitida{4}:{5}"
                    .format(len(new_itemlist), len(list_item), _filter.language, language_count,
                            _filter.quality_not_allowed, quality_count))

        if len(new_itemlist) == 0:
            # new_itemlist.append(Item(channel=__channel__, title="Obtener todos los servidores sin filtro",
            #                      url="", action="mainlist", show="kaka"))
            # new_itemlist = list_item
            # TODO CAMBIAR PARA QUE LLAME A GET_LINKS SIN FILTRO Y CAMBIAR CHANNEL Y ACTION??
            new_itemlist.append(Item(channel=channel, action="mainlist",
                                     title="[COLOR red]No se han encontrado items con el filtro [{0}] y ![{1}][/COLOR]"
                                     .format(_filter.language, _filter.quality_not_allowed), url="", thumbnail="",
                                     plot="", context="borrar filtro", show=list_item[0].show))
    else:
        new_itemlist = list_item

    return new_itemlist


def get_filtered_tvshows(from_channel):
    """
    Obtiene las series filtradas de un canal

    :param from_channel: canal que tiene las series filtradas
    :type from_channel: string
    :return: dict con las series
    :rtype: dict
    """
    logger.info("[filtertools.py] get_filtered_tvshows")
    dict_series = {}
    name_file = from_channel

    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))

    fname = os.path.join(config.get_data_path(), "settings_channels", name_file + "_data.json")

    data = read_file(fname)
    dict_data = jsontools.load_json(data)

    check_json_file(data, fname, dict_data)

    if TAG_TVSHOWS in dict_data:
        dict_series = dict_data[TAG_TVSHOWS]

    if DEBUG:
        logger.info("json_series: {0}".format(dict_series))

    return dict_series


def read_file(fname):
    """
    pythonic way to read from file
    @type fname: string
    @param fname: filename
    @rtype:   string
    @return:  data from filename.
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
    pythonic way to write a file

    @type  fname: string
    @param fname: filename.
    @type  data: string
    @param data: data to save.
    @type  message: string
    @param message: message to display.

    @rtype:   bool
    @return:  result of saving.
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
        message = "Error al guardar en disco"
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


def mainlist_filter(channel, list_idiomas, list_calidad):
    """
    Muestra una lista de las series filtradas

    @param channel: nombre del canal para obtener las series filtradas
    @type channel: string
    @param list_idiomas: lista de idiomas del canal
    @type list_idiomas: list
    @param list_calidad: lista de calidades del canal
    @type list_calidad: list
    @rtype:   list
    @return:  itemlist.
    """
    logger.info("[filtertools.py] mainlist_filter")
    itemlist = list([])
    dict_series = get_filtered_tvshows(channel)

    idx = 0
    for key in sorted(dict_series):
        tag_color = "green"
        if idx % 2 == 0:
            tag_color = "blue"
        idx += 1
        title = "Configurar [COLOR {0}][{1}][/COLOR]".format(tag_color, string.capwords(key))

        itemlist.append(Item(channel=__channel__, action="config_filter", title=title, show=key,
                             list_idiomas=list_idiomas, list_calidad=list_calidad, from_channel=channel))

    return itemlist


def config_filter(item):
    """
    muestra una serie filtrada para su configuración

    @param item: item
    @type item: item
    """
    logger.info("[filtertools.py] config_filter")
    logger.info("item {0}".format(item.tostring()))

    # OBTENEMOS LOS DATOS DEL JSON
    dict_series = get_filtered_tvshows(item.from_channel)

    lang_selected = dict_series.get(item.show.lower(), {}).get(TAG_LANGUAGE, 'Español')
    list_quality = dict_series.get(item.show.lower(), {}).get(TAG_QUALITY_NOT_ALLOWED, "")
    # logger.info("lang selected {}".format(lang_selected))
    # logger.info("list quality {}".format(list_quality))

    list_controls = [{
            "id": "serie",
            "type": "label",
            "label": string.capwords(item.show),
            "color": "",
            "enabled": True,
            "visible": True,
        },
        {
            "id": "language",
            "type": "list",
            "label": "Idioma",
            "color": "0xFFee66CC",
            "default": item.list_idiomas.index(lang_selected),
            "enabled": True,
            "visible": True,
            "lvalues": item.list_idiomas
        }
    ]

    if item.list_calidad:
        list_controls_calidad = [
            {
                "id": "textoCalidad",
                "type": "label",
                "label": "Calidad NO permitida",
                "color": "0xffC6C384",
                "enabled": True,
                "visible": True,
            },
        ]
        for element in sorted(item.list_calidad, key=str.lower):
            list_controls_calidad.append({
                "id": element,
                "type": "bool",
                "label": element,
                "default": (False, True)[element.lower() in list_quality],
                "enabled": True,
                "visible": True,
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
            "color": "0xffC6C384",
            "enabled": allow_delete,
            "visible": allow_delete,
        },
        {
            "id": "checkbox_deleted",
            "type": "bool",
            "label": "¿Borrar filtro?",
            "color": "",
            "default": False,
            "enabled": allow_delete,
            "visible": allow_delete,
        }
    ]
    list_controls.extend(list_controls_deleted_option)

    platformtools.show_channel_settings(list_controls=list_controls, caption="Filtrado de enlaces por Serie",
                                        callback='guardar_valores', item=item)


def guardar_valores(item, dict_data_saved):
    """
    Guarda los valores configurados en la ventana
    @param item: item
    @type item: item
    @param dict_data_saved: diccionario con los datos salvados
    @type dict_data_saved: dict
    """
    # Aqui tienes q gestionar los datos obtenidos del cuadro de dialogo
    if item and dict_data_saved:
        logger.debug('item: {0}\ndatos: {1}'.format(item.tostring(), dict_data_saved))

        # OBTENEMOS LOS DATOS DEL JSON
        dict_series = get_filtered_tvshows(item.from_channel)

        if dict_data_saved["checkbox_deleted"] != 1:
            logger.info("Se actualiza los datos")

            list_quality = []
            for id, value in dict_data_saved.items():
                if id in item.list_calidad and value:
                        list_quality.append(id.lower())

            lang_selected = item.list_idiomas[dict_data_saved[TAG_LANGUAGE]]
            dict_filter = {TAG_QUALITY_NOT_ALLOWED: list_quality, TAG_LANGUAGE: lang_selected}
            dict_series[item.show.strip().lower()] = dict_filter

            message = "FILTRO GUARDADO"

        else:
            logger.info("borrado")
            lang_selected = item.list_idiomas[dict_data_saved[TAG_LANGUAGE]]
            dict_series.pop(item.show.strip().lower(), None)

            message = "FILTRO ELIMINADO"

        fname, json_data = update_json_data(dict_series, item.from_channel)
        message = save_file(json_data, fname, message)

        heading = "{0} [{1}]".format(string.capwords(item.show), lang_selected)
        platformtools.dialog_notification(heading, message)



def update_json_data(dict_series, name_file):
    """
    actualiza el json_data de un fichero con el diccionario pasado

    @param dict_series: diccionario con las series
    @type dict_series: dict
    @type name_file: string
    @param name_file: nombre del fichero para guardar
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
    """
    salva el filtro a través del menú contextual
    @param item: item
    @type item: item
    """
    logger.info("[filtertools.py] save_filter")

    dict_series = get_filtered_tvshows(item.from_channel)

    name = item.show.strip().lower()
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

    message = "FILTRO GUARDADO"
    message = save_file(json_data, fname, message)

    heading = "{0} [1]".format(string.capwords(item.show.strip()), idioma)
    platformtools.dialog_notification(heading, message)


def del_filter(item):
    """
    elimina el filtro a través del menú contextual
    @param item: item
    @type item: item
    """
    logger.info("[filtertools.py] del_filter")

    dict_series = get_filtered_tvshows(item.from_channel)
    dict_series.pop(item.show.strip().lower(), None)

    fname, json_data = update_json_data(dict_series, item.from_channel)
    message = save_file(json_data, fname, "FILTRO Borrado")

    heading = "{0}".format(string.capwords(item.show.strip()))
    platformtools.dialog_notification(heading, message)
