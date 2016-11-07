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
# --------------------------------------------------------------------------------
# renumeratetools - se encarga de renumerar episodios
# --------------------------------------------------------------------------------

import os

import xbmcgui
from core import config
from core import filetools
from core import jsontools
from core import logger
from core.item import Item
from platformcode import platformtools


TAG_TVSHOW_RENUMERATE = "TVSHOW_RENUMBER"
TAG_SEASON_EPISODE = "season_episode"
__channel__ = "renumbertools"


def context():
    _context = ""
    '''
    configuración para mostrar la opción de renumeración, actualmente sólo se permite en xbmc, se cambiará cuando
    'platformtools.show_channel_settings' esté disponible para las distintas plataformas
    '''
    if config.is_xbmc():
        _context = [{"title": "RENUMERAR",
                     "action": "config_item",
                     "channel": "renumbertools"}]

    return _context

context = context()


def show_option(channel, itemlist):
    itemlist.append(Item(channel=__channel__, title="[COLOR yellow]Configurar renumeración en series...[/COLOR]",
                         action="load", from_channel=channel))

    return itemlist


def load(item):
    return mainlist(channel=item.from_channel)


def get_tvshows(from_channel):
    """
    Obtiene las series renumeradas de un canal

    :param from_channel: canal que tiene las series renumeradas
    :type from_channel: str
    :return: dict con las series
    :rtype: dict
    """
    logger.info()
    dict_series = {}
    name_file = from_channel

    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))

    fname = os.path.join(config.get_data_path(), "settings_channels", name_file + "_data.json")

    data = filetools.read(fname)
    dict_data = jsontools.load_json(data)

    check_json_file(data, fname, dict_data)

    if TAG_TVSHOW_RENUMERATE in dict_data:
        dict_series = dict_data[TAG_TVSHOW_RENUMERATE]

    logger.debug("json_series: {0}".format(dict_series))

    return dict_series


def mainlist(channel):
    """
    Muestra una lista de las series renumeradas

    :param channel: nombre del canal para obtener las series renumeradas
    :type channel: str
    :return: lista de Item
    :rtype: list[Item]
    """
    logger.info()
    itemlist = []
    dict_series = get_tvshows(channel)

    idx = 0
    for tvshow in sorted(dict_series):
        tag_color = "0xff008000"
        if idx % 2 == 0:
            tag_color = "blue"

        idx += 1
        name = tvshow
        title = "Configurar [COLOR {0}][{1}][/COLOR]".format(tag_color, name)

        itemlist.append(Item(channel=__channel__, action="config_item", title=title, show=name, from_channel=channel))

    if len(itemlist) == 0:
        itemlist.append(Item(channel=channel, action="mainlist",
                             title="No se han encontrado series, busca una serie y pulsa en menú contextual "
                                   "'RENUMERAR'"))

    return itemlist


def config_item(item):
    """
    muestra una serie renumerada para su configuración

    :param item: item
    :type item: Item
    """
    logger.info("item {0}".format(item.tostring("\n")))

    dict_series = get_tvshows(item.from_channel)
    data = dict_series.get(item.show, {})

    if data:
        data = data.get(TAG_SEASON_EPISODE, [])

        ventana = RenumberWindow(show=item.show, channel=item.from_channel, data=data)
        del ventana
    else:
        # tenemos información y devolvemos los datos añadidos para que se muestre en la ventana
        if data:
            return add_season(item.from_channel, item.show)
        # es la primera vez que se añaden datos (usando menú contextual) por lo que no devolvemos nada
        # para evitar error al listar los items
        else:
            add_season(item.from_channel, item.show)


def borrar(channel, show):
    logger.info()
    heading = "¿Está seguro que desea eliminar renumeración?"
    line1 = "Pulse 'Si' para eliminar la renumeración de [COLOR blue]{0}[/COLOR], pulse 'No' o cierre la ventana " \
            "para no hacer nada.".format(show.strip())

    if platformtools.dialog_yesno(heading, line1) == 1:
        dict_series = get_tvshows(channel)
        dict_series.pop(show, None)

        fname, json_data = update_json_data(dict_series, channel)
        result = filetools.write(fname, json_data)

        if result:
            message = "FILTRO ELIMINADO"
        else:
            message = "Error al guardar en disco"

        heading = show.strip()
        platformtools.dialog_notification(heading, message)


def add_season(channel, show):
    # logger.info("item {0}".format(item.tostring("\n")))

    # OBTENEMOS LOS DATOS DEL JSON
    dict_series = get_tvshows(channel)
    tvshow = show.strip()
    list_season_episode = dict_series.get(tvshow, {}).get(TAG_SEASON_EPISODE, [])
    logger.debug("item {0}".format(list_season_episode))
    heading = "Introduzca el número de la temporada"
    default = 2
    if list_season_episode:
        # mostrar temporada + 1 de la lista
        default = list_season_episode[0][0]+1

    season = platformtools.dialog_numeric(0, heading, str(default))

    # si hemos insertado un valor en la temporada
    if season != "" and int(season) > 0:
        heading = "Introduzca el número de episodio desde que empieza la temporada"
        default = 0
        if list_season_episode:
            for e in list_season_episode:
                # mostrar suma episodios de la lista
                default += e[1]
        episode = platformtools.dialog_numeric(0, heading, str(default))

        # si hemos insertado un valor en el episodio
        if episode != "":
            if list_season_episode:
                list_season_episode.insert(0, [int(season), int(episode)])
                new_list_season_episode = list_season_episode[:]
                dict_renumerate = {TAG_SEASON_EPISODE: new_list_season_episode}
            else:
                dict_renumerate = {TAG_SEASON_EPISODE: [[int(season), int(episode)]]}

            dict_series[tvshow] = dict_renumerate

            fname, json_data = update_json_data(dict_series, channel)
            result = filetools.write(fname, json_data)

            if result:
                message = "FILTRO GUARDADO"
                ok = True
            else:
                message = "Error al guardar en disco"
                ok = False

            heading = show.strip()
            platformtools.dialog_notification(heading, message)

            if ok:
                return dict_renumerate.get(TAG_SEASON_EPISODE)
            else:
                return None


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
    logger.info()
    if not dict_data:
        logger.error("Error al cargar el json del fichero {0}".format(fname))

        if data != "":
            # se crea un nuevo fichero
            title = filetools.write("{0}.bk".format(fname), data)
            if title != "":
                logger.error("Ha habido un error al guardar el fichero: {0}.bk"
                             .format(fname))
            else:
                logger.debug("Se ha guardado una copia con el nombre: {0}.bk"
                             .format(fname))
        else:
            logger.debug("Está vacío el fichero: {0}".format(fname))


def update_json_data(dict_series, filename):
    """
    actualiza el json_data de un fichero con el diccionario pasado

    :param dict_series: diccionario con las series
    :type dict_series: dict
    :param filename: nombre del fichero para guardar
    :type filename: str
    :return: fname, json_data
    :rtype: str, dict
    """
    logger.info()
    if not os.path.exists(os.path.join(config.get_data_path(), "settings_channels")):
        os.mkdir(os.path.join(config.get_data_path(), "settings_channels"))
    fname = os.path.join(config.get_data_path(), "settings_channels", filename + "_data.json")
    data = filetools.read(fname)
    dict_data = jsontools.load_json(data)
    # es un dict
    if dict_data:
        if TAG_TVSHOW_RENUMERATE in dict_data:
            logger.info("   existe el key SERIES")
            dict_data[TAG_TVSHOW_RENUMERATE] = dict_series
        else:
            logger.info("   NO existe el key SERIES")
            new_dict = {TAG_TVSHOW_RENUMERATE: dict_series}
            dict_data.update(new_dict)
    else:
        logger.info("   NO es un dict")
        dict_data = {TAG_TVSHOW_RENUMERATE: dict_series}
    json_data = jsontools.dump_json(dict_data)
    return fname, json_data


class RenumberWindow(xbmcgui.WindowDialog):
    ID_BUTTON_CLOSE = 3004
    ID_BUTTON_OK = 3008
    ID_BUTTON_CANCEL = 3009
    ID_BUTTON_DELETE = 3010
    ID_BUTTON_ADD_SEASON = 3011
    ID_BUTTON_INFO = 3012
    ID_CHECK_UPDATE_INTERNET = 3013

    def __init__(self, *args, **kwargs):
        logger.debug()
        self.show = kwargs.get("show")
        self.channel = kwargs.get("channel")
        self.data = kwargs.get("data")

        self.mediapath = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media')
        self.font = "font12"

        self.window_bg = xbmcgui.ControlImage(240, 110, 800, 500,
                                              os.path.join(self.mediapath, 'Windows', 'DialogBack.png'))
        self.addControl(self.window_bg)

        header_bg = xbmcgui.ControlImage(240, 110, 800, 40, os.path.join(self.mediapath, 'Windows', 'dialogheader.png'))
        self.addControl(header_bg)

        header_title = xbmcgui.ControlLabel(275, 125, 700, 34, self.show, font="font12_title", textColor="0xFFFFA500",
                                            alignment=2)
        self.addControl(header_title)

        self.btn_close = xbmcgui.ControlButton(975, 125, 50, 30, '',
                                               focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                         'DialogCloseButton-focus.png'),
                                               noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                           'DialogCloseButton.png'))
        self.addControl(self.btn_close)

        controls_bg = xbmcgui.ControlImage(260, 150, 745, 327,
                                           os.path.join(self.mediapath, 'Windows', 'BackControls.png'))
        self.addControl(controls_bg)

        scroll_bg = xbmcgui.ControlImage(1015, 150, 10, 327, os.path.join(self.mediapath, 'Controls', 'ScrollBack.png'))
        self.addControl(scroll_bg)

        scroll2_bg = xbmcgui.ControlImage(1015, 150, 10, 387, os.path.join(self.mediapath, 'Controls', 'ScrollBar.png'))
        self.addControl(scroll2_bg)

        self.btn_ok = xbmcgui.ControlButton(408, 550, 120, 30, 'OK', font=self.font,
                                            focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                      'KeyboardKey.png'),
                                            noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                        'KeyboardKeyNF.png'), alignment=4 | 2)
        self.addControl(self.btn_ok)

        self.btn_cancel = xbmcgui.ControlButton(578, 550, 120, 30, 'Cancelar', font=self.font,
                                                focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                          'KeyboardKey.png'),
                                                noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                            'KeyboardKeyNF.png'), alignment=4 | 2)
        self.addControl(self.btn_cancel)

        self.btn_delete = xbmcgui.ControlButton(748, 550, 120, 30, 'Borrar', font=self.font,
                                                focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                          'KeyboardKey.png'),
                                                noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                            'KeyboardKeyNF.png'), alignment=4 | 2)
        self.addControl(self.btn_delete)

        btn_add_season = xbmcgui.ControlButton(348, 492, 180, 30, 'Añadir Temporada', font=self.font,
                                               focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                         'KeyboardKey.png'),
                                               noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                           'KeyboardKeyNF.png'), alignment=4 | 2)
        self.addControl(btn_add_season)

        self.btn_info = xbmcgui.ControlButton(578, 492, 120, 30, 'Información', font=self.font,
                                              focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                        'KeyboardKey.png'),
                                              noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                          'KeyboardKeyNF.png'), alignment=4 | 2)
        self.addControl(self.btn_info)

        self.check_update_internet = xbmcgui.ControlRadioButton(748, 490, 235,
                                                                34, "Actualizar desde Internet:", font=self.font,
                                                                focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                          'MenuItemFO.png'),
                                                                noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                            'MenuItemNF.png'),
                                                                focusOnTexture=os.path.join(self.mediapath, 'Controls',
                                                                                            'radiobutton-focus.png'),
                                                                noFocusOnTexture=os.path.join(self.mediapath,
                                                                                              'Controls',
                                                                                              'radiobutton-focus.png'),
                                                                focusOffTexture=os.path.join(self.mediapath, 'Controls',
                                                                                             'radiobutton-nofocus.png'),
                                                                noFocusOffTexture=os.path.join(self.mediapath,
                                                                                               'Controls',
                                                                                               'radiobutton-nofocus.png'))
        self.addControl(self.check_update_internet)
        self.check_update_internet.setEnabled(False)

        window_bg = xbmcgui.ControlImage(260, 535, 760, 2,
                                         os.path.join(self.mediapath, 'Controls', 'ScrollBack.png'))
        self.addControl(window_bg)


        # self.setFocus(self.btn_informacion)
        self.onInit()

    def onInit(self, *args, **kwargs):
        if kwargs.get("data"):
            self.data = kwargs.get("data")
        logger.debug("mojonazo2")
        logger.debug("data %s" % self.data)
        try:

            # listado temporada / episodios
            pos_inicial_y = 160
            pos_y = pos_inicial_y

            # cambiamos el orden para que se vea en orden ascendente
            self.data.sort(key=lambda el: int(el[0]), reverse=False)

            for e in self.data:
                label_season = xbmcgui.ControlLabel(250, pos_y + 3, 150, 34, "Temporada:", font="font12_title",
                                                    textColor="0xFFFFA500",
                                                    alignment=2)
                self.addControl(label_season)

                text_season = xbmcgui.ControlTextBox(380, pos_y + 3, 100, 34, font="font12_title")
                self.addControl(text_season)
                text_season.setText(str(e[0]))

                label_episode = xbmcgui.ControlLabel(400, pos_y + 3, 150, 34, "Episodios:", font="font12_title",
                                                     textColor="0xFFFFA500",
                                                     alignment=2)
                self.addControl(label_episode)

                text_episode = xbmcgui.ControlTextBox(520, pos_y + 3, 700, 34, font="font12_title")
                self.addControl(text_episode)
                text_episode.setText(str(e[1]))

                btn_eliminar = xbmcgui.ControlButton(870, pos_y, 120, 30, 'Eliminar', font=self.font,
                                                     focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                               'KeyboardKey.png'),
                                                     noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                 'KeyboardKeyNF.png'), alignment=4 | 2)
                self.addControl(btn_eliminar)

                window_bg = xbmcgui.ControlImage(270, pos_y + 40, 725, 2,
                                                 os.path.join(self.mediapath, 'Controls', 'ScrollBack.png'))
                self.addControl(window_bg)

                pos_y += 50
            pass


        except Exception, Ex:
            logger.error("HA HABIDO UNA HOSTIA %s" % Ex)
            pass
        self.doModal()
        pass

    def onClick(self, control_id):
        logger.debug("NO FUNCIONA control_id" + control_id)
        pass

    def onFocus(self, control_id):
        logger.debug("control_id" + control_id)
        pass

    def onControl(self, control):
        logger.debug("mierda control: %s" % control.getId())
        control_id = control.getId()

        if control_id == self.ID_BUTTON_OK:
            pass
        if control_id in [self.ID_BUTTON_CLOSE, self.ID_BUTTON_CANCEL]:
            self.close()
        elif control_id == self.ID_BUTTON_DELETE:
            self.close()
            borrar(self.channel, self.show)
        elif control_id == self.ID_BUTTON_ADD_SEASON:
            data = add_season(self.channel, self.show)
            # se ha producido un error al guardar los datos, volvemos a enviar los datos que teníamos
            if data is None:
                data = self.data
            self.onInit(data=data)
        elif control_id == self.ID_BUTTON_INFO:
            self.method_info()

    def onAction(self, action):
        logger.debug("action %s" % action.getId())

        # Obtenemos el foco
        focus = self.getFocusId()

        action = action.getId()
        # Accion 1: Flecha izquierda
        if action == 1:
            # Si el foco no está en ninguno de los 6 botones inferiores, y esta en un "list" cambiamos el valor
            if focus not in [self.ID_BUTTON_ADD_SEASON, self.ID_BUTTON_INFO, self.ID_CHECK_UPDATE_INTERNET,
                             self.ID_BUTTON_OK, self.ID_BUTTON_CANCEL, self.ID_BUTTON_DELETE]:
                pass
                # control = self.getFocus()
                # for cont in self.controls:
                #     if cont["type"] == "list" and cont["control"] == control:
                #         index = cont["lvalues"].index(cont["label"].getLabel())
                #         if index < len(cont["lvalues"]) - 1:
                #             cont["label"].setLabel(cont["lvalues"][index + 1])
                #
                #         # Guardamos el nuevo valor en el listado de controles
                #         self.values[cont["id"]] = cont["lvalues"].index(cont["label"].getLabel())

            # Si el foco está en alguno de los 6 botones inferiores, movemos al siguiente
            else:
                if focus in [self.ID_BUTTON_ADD_SEASON, self.ID_BUTTON_INFO, self.ID_CHECK_UPDATE_INTERNET]:
                    if focus == self.ID_BUTTON_ADD_SEASON:
                        pass
                        # vamos al ultimo control
                    elif focus == self.ID_BUTTON_INFO:
                        self.setFocusId(self.ID_BUTTON_ADD_SEASON)
                    elif focus == self.ID_CHECK_UPDATE_INTERNET:
                        self.setFocusId(self.ID_BUTTON_INFO)

                elif focus in [self.ID_BUTTON_OK, self.ID_BUTTON_CANCEL, self.ID_BUTTON_DELETE]:
                    if focus == self.ID_BUTTON_OK:
                        self.setFocusId(self.ID_BUTTON_INFO)
                        # TODO cambiar cuando se habilite la opcion de actualizar por internet
                        # self.setFocusId(self.ID_CHECK_UPDATE_INTERNET)
                    elif focus == self.ID_BUTTON_CANCEL:
                        self.setFocusId(self.ID_BUTTON_OK)
                    elif focus == self.ID_BUTTON_DELETE:
                        self.setFocusId(self.ID_BUTTON_CANCEL)

        # Accion 2: Flecha derecha
        elif action == 2:
            # Si el foco no está en ninguno de los 6 botones inferiores, y esta en un "list" cambiamos el valor
            if focus not in [self.ID_BUTTON_ADD_SEASON, self.ID_BUTTON_INFO, self.ID_CHECK_UPDATE_INTERNET,
                             self.ID_BUTTON_OK, self.ID_BUTTON_CANCEL, self.ID_BUTTON_DELETE]:
                pass
                # control = self.getFocus()
                # for cont in self.controls:
                #     if cont["type"] == "list" and cont["control"] == control:
                #         index = cont["lvalues"].index(cont["label"].getLabel())
                #         if index > 0:
                #             cont["label"].setLabel(cont["lvalues"][index - 1])
                #
                #         # Guardamos el nuevo valor en el listado de controles
                #         self.values[cont["id"]] = cont["lvalues"].index(cont["label"].getLabel())

            # Si el foco está en alguno de los 6 botones inferiores, movemos al siguiente
            else:
                if focus in [self.ID_BUTTON_ADD_SEASON, self.ID_BUTTON_INFO, self.ID_CHECK_UPDATE_INTERNET]:
                    if focus == self.ID_BUTTON_ADD_SEASON:
                        self.setFocusId(self.ID_BUTTON_INFO)
                    if focus == self.ID_BUTTON_INFO:
                        self.setFocusId(self.ID_BUTTON_OK)
                        # TODO cambiar cuando se habilite la opcion de actualizar por internet
                        # self.setFocusId(self.ID_CHECK_UPDATE_INTERNET)
                    if focus == self.ID_CHECK_UPDATE_INTERNET:
                        self.setFocusId(self.ID_BUTTON_OK)

                elif focus in [self.ID_BUTTON_OK, self.ID_BUTTON_CANCEL, self.ID_BUTTON_DELETE]:
                    if focus == self.ID_BUTTON_OK:
                        self.setFocusId(self.ID_BUTTON_CANCEL)
                    if focus == self.ID_BUTTON_CANCEL:
                        self.setFocusId(self.ID_BUTTON_DELETE)
                    if focus == self.ID_BUTTON_DELETE:
                        # vamos al primer control
                        pass

        # Accion 3: Flecha arriba
        elif action == 3:
            self.move_up(focus)
        # Accion 4: Flecha abajo
        elif action == 4:
            self.move_down(focus)
        # ACTION_MOUSE_WHEEL_UP = 104
        elif action == 104:
            self.move_up(focus)
        # ACTION_MOUSE_WHEEL_DOWN = 105
        elif action == 105:
            self.move_down(focus)


        # ACTION_PAGE_DOWN = 6
        # ACTION_PAGE_UP = 5


        # ACTION_PREVIOUS_MENU = 10
        # ACTION_NAV_BACK = 92
        elif action in [10, 92]:
            self.close()

        logger.debug("el foco lo tiene " + str(focus))

    def move_down(self, focus):
        # Si el foco está en uno de los tres botones medios, bajamos el foco a la otra linea de botones
        if focus in [self.ID_BUTTON_ADD_SEASON, self.ID_BUTTON_INFO, self.ID_CHECK_UPDATE_INTERNET]:
            if focus == self.ID_BUTTON_ADD_SEASON:
                self.setFocusId(self.ID_BUTTON_OK)
            elif focus == self.ID_BUTTON_INFO:
                self.setFocusId(self.ID_BUTTON_CANCEL)
            elif focus == self.ID_CHECK_UPDATE_INTERNET:
                self.setFocusId(self.ID_BUTTON_DELETE)
        # Si el foco está en uno de los tres botones inferiores, subimos el foco al primer control del listado
        elif focus in [self.ID_BUTTON_OK, self.ID_BUTTON_CANCEL, self.ID_BUTTON_DELETE]:
            pass
        # nos movemos entre los elementos del listado
        else:
            pass

    def move_up(self, focus):
        # Si el foco está en uno de los tres botones medios, subimos el foco al último control del listado
        if focus in [self.ID_BUTTON_ADD_SEASON, self.ID_BUTTON_INFO, self.ID_CHECK_UPDATE_INTERNET]:
            pass
        # Si el foco está en uno de los tres botones inferiores, subimos el foco a la otra linea de botones
        elif focus in [self.ID_BUTTON_OK, self.ID_BUTTON_CANCEL, self.ID_BUTTON_DELETE]:
            if focus == self.ID_BUTTON_OK:
                self.setFocusId(self.ID_BUTTON_ADD_SEASON)
            elif focus == self.ID_BUTTON_CANCEL:
                self.setFocusId(self.ID_BUTTON_INFO)
            elif focus == self.ID_BUTTON_DELETE:
                self.setFocusId(self.ID_BUTTON_INFO)
                # TODO cambiar cuando se habilite la opcion de actualizar por internet
                # self.setFocusId(self.ID_CHECK_UPDATE_INTERNET)
        # nos movemos entre los elementos del listado
        else:
            pass

    @staticmethod
    def method_info():
        title = "Información"
        text = "La primera temporada que se añade siempre empieza en \"0\" episodios, la segunda temporada que se "
        text += "añade empieza en el número total de episodios de la primera temporada, la tercera temporada será "
        text += "la suma de los episodios de las temporadas previas y así sucesivamente.\n"
        text += "[COLOR blue]\nEjemplo de serie divida en varias temporadas:\n"
        text += "\nFairy Tail:\n"
        text += "  - SEASON 1: EPISODE 48 --> [season 1, episode: 0]\n"
        text += "  - SEASON 2: EPISODE 48 --> [season 2, episode: 48]\n"
        text += "  - SEASON 3: EPISODE 54 --> [season 3, episode: 96 ([48=season2] + [48=season1])]\n"
        text += "  - SEASON 4: EPISODE 175 --> [season 4: episode: 150 ([54=season3] + [48=season2] + [48=season3" \
                "])][/COLOR]\n"
        text += "[COLOR green]\nEjemplo de serie que es la segunda temporada de la original:\n"
        text += "\nFate/Zero 2nd Season:\n"
        text += "  - SEASON 1: EPISODE 12 --> [season 2, episode: 0][/COLOR]\n"

        return TextBox("DialogTextViewer.xml", os.getcwd(), "Default", title=title, text=text)


class TextBox(xbmcgui.WindowXMLDialog):
    """ Create a skinned textbox window """
    def __init__(self, *args, **kwargs):
        self.title = kwargs.get('title')
        self.text = kwargs.get('text')
        self.doModal()

    def onInit(self):
        try:
            self.getControl(5).setText(self.text)
            self.getControl(1).setLabel(self.title)
        except:
            pass

    def onClick(self, control_id):
        pass

    def onFocus(self, control_id):
        pass

    def onAction(self, action):
        self.close()
