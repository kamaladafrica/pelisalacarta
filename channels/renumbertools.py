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

# Align
ALIGN_LEFT = 0
ALIGN_RIGHT = 1
ALIGN_CENTER_X = 2
ALIGN_CENTER_Y = 4
ALIGN_CENTER = 6
ALIGN_TRUNCATED = 8
ALIGN_JUSTIFY = 10

# button ids
ID_BUTTON_CLOSE = 3003
ID_BUTTON_ADD_SEASON = 3008
ID_BUTTON_INFO = 3009
ID_CHECK_UPDATE_INTERNET = 3010
ID_BUTTON_OK = 3012
ID_BUTTON_CANCEL = 3013
ID_BUTTON_DELETE = 3014


class RenumberWindow(xbmcgui.WindowDialog):

    def __init__(self, *args, **kwargs):
        logger.debug()

        if xbmcgui.__version__ == "1.2":
            self.setCoordinateResolution(1)
        else:
            self.setCoordinateResolution(5)

        self.show = kwargs.get("show")
        self.channel = kwargs.get("channel")
        self.data = kwargs.get("data")

        self.mediapath = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media')
        self.font = "font12"

        window_bg = xbmcgui.ControlImage(320, 130, 600, 440, os.path.join(self.mediapath, 'Windows', 'DialogBack.png'))
        self.addControl(window_bg)

        header_bg = xbmcgui.ControlImage(window_bg.getX(), window_bg.getY() + 8, window_bg.getWidth(), 35,
                                         os.path.join(self.mediapath, 'Windows', 'dialogheader.png'))
        self.addControl(header_bg)

        btn_close_w = 64
        self.btn_close = xbmcgui.ControlButton(window_bg.getX() + window_bg.getWidth() - btn_close_w - 13,
                                               header_bg.getY() + 6, btn_close_w, 30, '',
                                               focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                         'DialogCloseButton-focus.png'),
                                               noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                           'DialogCloseButton.png'))
        self.addControl(self.btn_close)

        header_title_x = window_bg.getX() + 20
        header_title = xbmcgui.ControlFadeLabel(header_title_x, header_bg.getY() + 5, self.btn_close.getX() -
                                                header_title_x, 30, font="font12_title", textColor="0xFFFFA500",
                                                _alignment=ALIGN_CENTER)
        self.addControl(header_title)
        header_title.addLabel(self.show)

        self.controls_bg = xbmcgui.ControlImage(window_bg.getX() + 20, header_bg.getY() + header_bg.getHeight() + 6,
                                                562, 260, os.path.join(self.mediapath, 'Windows', 'BackControls.png'))
        self.addControl(self.controls_bg)

        self.scroll_bg = xbmcgui.ControlImage(window_bg.getX() + window_bg.getWidth() - 25, self.controls_bg.getY(), 10,
                                              self.controls_bg.getHeight(), os.path.join(self.mediapath, 'Controls',
                                                                                         'ScrollBack.png'))
        self.addControl(self.scroll_bg)
        self.scroll_bg.setVisible(False)

        self.scroll2_bg = xbmcgui.ControlImage(window_bg.getX() + window_bg.getWidth() - 25, self.controls_bg.getY(),
                                               10, self.controls_bg.getHeight(), os.path.join(self.mediapath,
                                                                                              'Controls',
                                                                                              'ScrollBar.png'))
        self.addControl(self.scroll2_bg)
        self.scroll2_bg.setVisible(False)

        btn_add_season = xbmcgui.ControlButton(window_bg.getX() + 20, self.controls_bg.getY() +
                                               self.controls_bg.getHeight() + 14, 165, 30, 'Añadir Temporada',
                                               font=self.font, focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                         'KeyboardKey.png'),
                                               noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                           'KeyboardKeyNF.png'), alignment=ALIGN_CENTER)
        self.addControl(btn_add_season)

        self.btn_info = xbmcgui.ControlButton(window_bg.getX() + 210, btn_add_season.getY(), 120, 30, 'Información',
                                              font=self.font, focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                        'KeyboardKey.png'),
                                              noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                          'KeyboardKeyNF.png'), alignment=ALIGN_CENTER)
        self.addControl(self.btn_info)

        check_update_internet_w = 235
        # Versiones antiguas no admite algunas texturas
        if xbmcgui.__version__ in["1.2", "2.0"]:
            self.check_update_internet = xbmcgui.ControlRadioButton(
                window_bg.getX() + window_bg.getWidth() - check_update_internet_w - 20, btn_add_season.getY() - 3,
                check_update_internet_w, 34, "Actualizar desde Internet:", font=self.font,
                focusTexture=os.path.join(self.mediapath, 'Controls', 'MenuItemFO.png'),
                noFocusTexture=os.path.join(self.mediapath, 'Controls', 'MenuItemNF.png'))
        else:
            self.check_update_internet = xbmcgui.ControlRadioButton(
                window_bg.getX() + window_bg.getWidth() - check_update_internet_w - 20, btn_add_season.getY() - 3,
                check_update_internet_w, 34, "Actualizar desde Internet:", font=self.font,
                focusTexture=os.path.join(self.mediapath, 'Controls', 'MenuItemFO.png'),
                noFocusTexture=os.path.join(self.mediapath, 'Controls', 'MenuItemNF.png'),
                focusOnTexture=os.path.join(self.mediapath, 'Controls', 'radiobutton-focus.png'),
                noFocusOnTexture=os.path.join(self.mediapath, 'Controls', 'radiobutton-focus.png'),
                focusOffTexture=os.path.join(self.mediapath, 'Controls', 'radiobutton-nofocus.png'),
                noFocusOffTexture=os.path.join(self.mediapath, 'Controls', 'radiobutton-nofocus.png'))

        self.addControl(self.check_update_internet)
        self.check_update_internet.setEnabled(False)

        hb_bg = xbmcgui.ControlImage(window_bg.getX() + 20, btn_add_season.getY() + btn_add_season.getHeight() + 13,
                                     window_bg.getWidth() - 40, 2,
                                     os.path.join(self.mediapath, 'Controls', 'ScrollBack.png'))
        self.addControl(hb_bg)

        self.btn_ok = xbmcgui.ControlButton(window_bg.getX() + 68, hb_bg.getY() + hb_bg.getHeight() + 13, 120, 30,
                                            'OK', font=self.font,
                                            focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                      'KeyboardKey.png'),
                                            noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                        'KeyboardKeyNF.png'), alignment=ALIGN_CENTER)
        self.addControl(self.btn_ok)

        self.btn_cancel = xbmcgui.ControlButton(self.btn_info.getX()+30, self.btn_ok.getY(), 120, 30, 'Cancelar',
                                                font=self.font, focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                          'KeyboardKey.png'),
                                                noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                            'KeyboardKeyNF.png'),
                                                alignment=ALIGN_CENTER)
        self.addControl(self.btn_cancel)

        self.btn_delete = xbmcgui.ControlButton(self.btn_cancel.getX() + self.btn_cancel.getWidth() + 50,
                                                self.btn_ok.getY(), 120, 30, 'Borrar', font=self.font,
                                                focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                          'KeyboardKey.png'),
                                                noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                            'KeyboardKeyNF.png'),
                                                alignment=ALIGN_CENTER)
        self.addControl(self.btn_delete)

        self.controls = []
        self.onInit()
        logger.debug("seteo el foco por primera vez [0][0]")
        self.setFocus(self.controls[0][0])
        self.doModal()

    def onInit(self, *args, **kwargs):
        if kwargs.get("data"):
            self.data = kwargs.get("data")
        try:

            # listado temporada / episodios
            pos_y = self.controls_bg.getY() + 10

            # cambiamos el orden para que se vea en orden ascendente
            self.data.sort(key=lambda el: int(el[0]), reverse=False)

            # mostramos el scroll si hay más de 5 elementos
            if len(self.data) > 5:
                self.controls_bg.setWidth(545)
                self.scroll_bg.setVisible(True)
                self.scroll2_bg.setVisible(True)

            self.controls = []

            for index, e in enumerate(self.data):
                pos_x = self.controls_bg.getX() + 15
                label_season_w = 100
                label_season = xbmcgui.ControlLabel(pos_x, pos_y + 3, label_season_w, 34,
                                                    "Temporada:", font=self.font, textColor="0xFF2E64FE")
                self.addControl(label_season)
                logger.debug("ID label season[{}]:{} ".format(index, label_season.getId()))

                pos_x += label_season_w + 5

                # TODO mirar retro-compatilibidad
                # if xbmcgui.ControlEdit == ControlEdit:
                #       edit_season = xbmcgui.ControlEdit(0, 0, 0, 0, '', font=self.font, isPassword=False,
                #                                         textColor='',
                #                                         focusTexture=os.path.join(self.mediapath, 'Controls',
                #                                                                   'MenuItemFO.png'),
                #                                         noFocusTexture=os.path.join(self.mediapath, 'Controls',
                #                                                                     'MenuItemNF.png'), window=self)
                # else:

                # control bugeado se tiene que usar metodos sets para que se cree correctamente.
                edit_season = xbmcgui.ControlEdit(0, 0, 0, 0, "", self.font, "",  '', 4, isPassword=False,
                                                  focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                            'MenuItemFO.png'),
                                                  noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                              'MenuItemNF.png'))
                self.addControl(edit_season)
                edit_season.setText(str(e[0]))
                # edit_season.setLabel("Temporada:", font=self.font, textColor="0xFF2E64FE")
                edit_season.setPosition(pos_x, pos_y - 2)
                edit_season.setWidth(25)
                edit_season.setHeight(35)

                label_episode_w = 90
                pos_x += edit_season.getWidth() + 60
                label_episode = xbmcgui.ControlLabel(pos_x, pos_y + 3, label_episode_w, 34, "Episodios:",
                                                     font=self.font, textColor="0xFF2E64FE")
                self.addControl(label_episode)

                pos_x += label_episode_w + 5
                # control bugeado se tiene que usar metodos sets para que se cree correctamente.
                edit_episode = xbmcgui.ControlEdit(0, 0, 0, 0, "", self.font, "",  '', 4, isPassword=False,
                                                   focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                             'MenuItemFO.png'),
                                                   noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                               'MenuItemNF.png'))
                self.addControl(edit_episode)
                edit_episode.setText(str(e[1]))
                # edit_episode.setLabel("Episodios:", font=self.font, textColor="0xFF2E64FE")
                edit_episode.setPosition(pos_x, pos_y - 2)
                edit_episode.setWidth(40)
                edit_episode.setHeight(35)

                btn_delete_season_w = 120
                btn_delete_season = xbmcgui.ControlButton(self.controls_bg.getX() + self.controls_bg.getWidth() -
                                                          btn_delete_season_w - 14, pos_y, btn_delete_season_w, 30,
                                                          'Eliminar', font=self.font,
                                                          focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                    'KeyboardKey.png'),
                                                          noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                                      'KeyboardKeyNF.png'),
                                                          alignment=ALIGN_CENTER)
                self.addControl(btn_delete_season)

                hb_bg = xbmcgui.ControlImage(self.controls_bg.getX() + 10, pos_y + 40, self.controls_bg.getWidth() - 20,
                                             2, os.path.join(self.mediapath, 'Controls', 'ScrollBack.png'))
                self.addControl(hb_bg)

                pos_y += 50

                if index > 4:
                    logger.debug("seteo como False")
                    label_season.setVisible(False)
                    edit_season.setVisible(False)
                    label_episode.setVisible(False)
                    edit_episode.setVisible(False)
                    btn_delete_season.setVisible(False)
                    hb_bg.setVisible(False)

                line = [edit_season, edit_episode, btn_delete_season]

                self.controls.append(line)

        except Exception, Ex:
            logger.error("HA HABIDO UNA HOSTIA %s" % Ex)
            pass
        # self.doModal()
        pass

    def onClick(self, control_id):
        logger.debug("NO FUNCIONA control_id" + control_id)
        pass

    def onFocus(self, control_id):
        logger.debug("control_id" + control_id)
        pass

    def onControl(self, control):
        logger.debug("%s" % control.getId())
        control_id = control.getId()

        if control_id == ID_BUTTON_OK:
            pass
        if control_id in [ID_BUTTON_CLOSE, ID_BUTTON_CANCEL]:
            self.close()
        elif control_id == ID_BUTTON_DELETE:
            self.close()
            borrar(self.channel, self.show)
        elif control_id == ID_BUTTON_ADD_SEASON:
            data = add_season(self.channel, self.show)
            # se ha producido un error al guardar los datos, volvemos a enviar los datos que teníamos
            if data is None:
                data = self.data
            self.onInit(data=data)
        elif control_id == ID_BUTTON_INFO:
            self.method_info()
        else:
            for x, linea in enumerate(self.controls):
                if control_id == self.controls[x][2].getId():
                    logger.debug("estoy dentrooooo")
                    # self.data.del
                    break

    def onAction(self, action):
        logger.debug("%s" % action.getId())
        logger.debug("focus %s" % self.getFocusId())
        # Obtenemos el foco
        focus = self.getFocusId()

        action = action.getId()
        # Flecha izquierda
        if action == xbmcgui.ACTION_MOVE_LEFT:
            # Si el foco no está en ninguno de los 6 botones inferiores, y esta en un "list" cambiamos el valor
            if focus not in [ID_BUTTON_ADD_SEASON, ID_BUTTON_INFO, ID_CHECK_UPDATE_INTERNET,
                             ID_BUTTON_OK, ID_BUTTON_CANCEL, ID_BUTTON_DELETE]:
                # Localizamos en el listado de controles el control que tiene el focus
                # todo mirar tema del cursor en el valor al desplazar lateralmente
                for x, linea in enumerate(self.controls):
                    for y, el in enumerate(linea):
                        if el.getId() == focus:
                            logger.debug("x:{} y:{} controls.length:{} linea.length:{}".format(x, y, len(self.controls),
                                                                                               len(linea)))
                            if y > 0:
                                self.setFocus(self.controls[x][y-1])
                            else:
                                self.setFocus(self.controls[x][len(linea) - 1])
                            return

            # Si el foco está en alguno de los 6 botones inferiores, movemos al siguiente
            else:
                if focus in [ID_BUTTON_ADD_SEASON, ID_BUTTON_INFO, ID_CHECK_UPDATE_INTERNET]:
                    if focus == ID_BUTTON_ADD_SEASON:
                        pass
                        # vamos al ultimo control
                    elif focus == ID_BUTTON_INFO:
                        self.setFocusId(ID_BUTTON_ADD_SEASON)
                    elif focus == ID_CHECK_UPDATE_INTERNET:
                        self.setFocusId(ID_BUTTON_INFO)

                elif focus in [ID_BUTTON_OK, ID_BUTTON_CANCEL, ID_BUTTON_DELETE]:
                    if focus == ID_BUTTON_OK:
                        self.setFocusId(ID_BUTTON_INFO)
                        # TODO cambiar cuando se habilite la opcion de actualizar por internet
                        # self.setFocusId(ID_CHECK_UPDATE_INTERNET)
                    elif focus == ID_BUTTON_CANCEL:
                        self.setFocusId(ID_BUTTON_OK)
                    elif focus == ID_BUTTON_DELETE:
                        self.setFocusId(ID_BUTTON_CANCEL)

        # Flecha derecha
        elif action == xbmcgui.ACTION_MOVE_RIGHT:
            # Si el foco no está en ninguno de los 6 botones inferiores, y esta en un "list" cambiamos el valor
            if focus not in [ID_BUTTON_ADD_SEASON, ID_BUTTON_INFO, ID_CHECK_UPDATE_INTERNET,
                             ID_BUTTON_OK, ID_BUTTON_CANCEL, ID_BUTTON_DELETE]:
                # Localizamos en el listado de controles el control que tiene el focus
                # todo mirar tema del cursor en el valor al desplazar lateralmente
                for x, linea in enumerate(self.controls):
                    for y, el in enumerate(linea):
                        if el.getId() == focus:
                            logger.debug("x:{} controls.length:{}".format(x, len(self.controls)))
                            if y < len(linea) - 1:
                                self.setFocus(self.controls[x][y+1])
                            else:
                                self.setFocus(self.controls[x][0])
                            return

            # Si el foco está en alguno de los 6 botones inferiores, movemos al siguiente
            else:
                if focus in [ID_BUTTON_ADD_SEASON, ID_BUTTON_INFO, ID_CHECK_UPDATE_INTERNET]:
                    if focus == ID_BUTTON_ADD_SEASON:
                        self.setFocusId(ID_BUTTON_INFO)
                    if focus == ID_BUTTON_INFO:
                        self.setFocusId(ID_BUTTON_OK)
                        # TODO cambiar cuando se habilite la opcion de actualizar por internet
                        # self.setFocusId(ID_CHECK_UPDATE_INTERNET)
                    if focus == ID_CHECK_UPDATE_INTERNET:
                        self.setFocusId(ID_BUTTON_OK)

                elif focus in [ID_BUTTON_OK, ID_BUTTON_CANCEL, ID_BUTTON_DELETE]:
                    if focus == ID_BUTTON_OK:
                        self.setFocusId(ID_BUTTON_CANCEL)
                    if focus == ID_BUTTON_CANCEL:
                        self.setFocusId(ID_BUTTON_DELETE)
                    if focus == ID_BUTTON_DELETE:
                        # vamos al primer control
                        pass

        # Flecha arriba
        elif action == xbmcgui.ACTION_MOVE_UP:
            self.move_up(focus)
        # Flecha abajo
        elif action == xbmcgui.ACTION_MOVE_DOWN:
            self.move_down(focus)
        # scroll up
        elif action == xbmcgui.ACTION_MOUSE_WHEEL_UP:
            self.move_up(focus)
        # scroll down
        elif action == xbmcgui.ACTION_MOUSE_WHEEL_DOWN:
            self.move_down(focus)

        # ACTION_PAGE_DOWN = 6
        # ACTION_PAGE_UP = 5

        # Menú previo o Atrás
        elif action in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK]:
            self.close()

    def move_down(self, focus):
        logger.debug("focus " + str(focus))
        # Si el foco está en uno de los tres botones medios, bajamos el foco a la otra linea de botones
        if focus in [ID_BUTTON_ADD_SEASON, ID_BUTTON_INFO, ID_CHECK_UPDATE_INTERNET]:
            if focus == ID_BUTTON_ADD_SEASON:
                self.setFocusId(ID_BUTTON_OK)
            elif focus == ID_BUTTON_INFO:
                self.setFocusId(ID_BUTTON_CANCEL)
            elif focus == ID_CHECK_UPDATE_INTERNET:
                self.setFocusId(ID_BUTTON_DELETE)
        # Si el foco está en uno de los tres botones inferiores, subimos el foco al primer control del listado
        elif focus in [ID_BUTTON_OK, ID_BUTTON_CANCEL, ID_BUTTON_DELETE]:
            if focus == ID_BUTTON_OK:
                self.setFocus(self.controls[0][0])
            elif focus == ID_BUTTON_CANCEL:
                self.setFocus(self.controls[0][1])
            elif focus == ID_BUTTON_DELETE:
                self.setFocus(self.controls[0][2])
        # nos movemos entre los elementos del listado
        else:
            # Localizamos en el listado de controles el control que tiene el focus
            for x, linea in enumerate(self.controls):
                for y, el in enumerate(linea):
                    if el.getId() == focus:
                        logger.debug("x:{} controls.length:{}".format(x, len(self.controls)))
                        if x+1 < len(self.controls):
                            self.scroll()

                            self.setFocus(self.controls[x+1][y])
                        else:
                            if y == 0:
                                self.setFocusId(ID_BUTTON_ADD_SEASON)
                            elif y == 1:
                                self.setFocusId(ID_BUTTON_INFO)
                            elif y == 2:
                                self.setFocusId(ID_BUTTON_INFO)
                                # TODO cambiar cuando se habilite la opcion de actualizar por internet
                                # self.setFocusId(ID_CHECK_UPDATE_INTERNET)
                        return

    def move_up(self, focus):
        # Si el foco está en uno de los tres botones medios, subimos el foco al último control del listado
        if focus in [ID_BUTTON_ADD_SEASON, ID_BUTTON_INFO, ID_CHECK_UPDATE_INTERNET]:
            # TODO buscar el ultimo elemento visible
            if len(self.controls) < 6:
                last_visible = len(self.controls) - 1
            else:
                last_visible = len(self.controls) - 3
            if focus == ID_BUTTON_ADD_SEASON:
                self.setFocus(self.controls[last_visible][0])
            elif focus == ID_BUTTON_INFO:
                self.setFocus(self.controls[last_visible][1])
            elif focus == ID_CHECK_UPDATE_INTERNET:
                self.setFocus(self.controls[last_visible][2])
        # Si el foco está en uno de los tres botones inferiores, subimos el foco a la otra linea de botones
        elif focus in [ID_BUTTON_OK, ID_BUTTON_CANCEL, ID_BUTTON_DELETE]:
            if focus == ID_BUTTON_OK:
                self.setFocusId(ID_BUTTON_ADD_SEASON)
            elif focus == ID_BUTTON_CANCEL:
                self.setFocusId(ID_BUTTON_INFO)
            elif focus == ID_BUTTON_DELETE:
                self.setFocusId(ID_BUTTON_INFO)
                # TODO cambiar cuando se habilite la opcion de actualizar por internet
                # self.setFocusId(ID_CHECK_UPDATE_INTERNET)
        # nos movemos entre los elementos del listado
        else:
            # Localizamos en el listado de controles el control que tiene el focus
            for x, linea in enumerate(self.controls):
                for y, el in enumerate(linea):
                    if el.getId() == focus:
                        logger.debug("x:{} controls.length:{}".format(x, len(self.controls)))
                        if x > 0:
                            self.scroll()

                            self.setFocus(self.controls[x-1][y])
                        else:
                            if y == 0:
                                self.setFocusId(ID_BUTTON_OK)
                            elif y == 1:
                                self.setFocusId(ID_BUTTON_CANCEL)
                            elif y == 2:
                                self.setFocusId(ID_BUTTON_DELETE)
                        return

    def scroll(self):
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

# TODO mirar retro-compatiblidad
# class ControlEdit(xbmcgui.ControlButton):
#     def __new__(self, *args, **kwargs):
#         del kwargs["isPassword"]
#         del kwargs["window"]
#         args = list(args)
#         return xbmcgui.ControlButton.__new__(self, *args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         self.isPassword = kwargs["isPassword"]
#         self.window = kwargs["window"]
#         self.label = ""
#         self.text = ""
#         self.textControl = xbmcgui.ControlLabel(self.getX(), self.getY(), self.getWidth(), self.getHeight(),
#                                                 self.text,
#                                                 font=kwargs["font"], textColor=kwargs["textColor"], alignment=4 | 1)
#         self.window.addControl(self.textControl)
#
#     def setLabel(self, val):
#         self.label = val
#         xbmcgui.ControlButton.setLabel(self, val)
#
#     def getX(self):
#         return xbmcgui.ControlButton.getPosition(self)[0]
#
#     def getY(self):
#         return xbmcgui.ControlButton.getPosition(self)[1]
#
#     def setEnabled(self, e):
#         xbmcgui.ControlButton.setEnabled(self, e)
#         self.textControl.setEnabled(e)
#
#     def setWidth(self, w):
#         xbmcgui.ControlButton.setWidth(self, w)
#         self.textControl.setWidth(w / 2)
#
#     def setHeight(self, w):
#         xbmcgui.ControlButton.setHeight(self, w)
#         self.textControl.setHeight(w)
#
#     def setPosition(self, x, y):
#         xbmcgui.ControlButton.setPosition(self, x, y)
#         self.textControl.setPosition(x + self.getWidth() / 2, y)
#
#     def setText(self, text):
#         self.text = text
#         if self.isPassword:
#             self.textControl.setLabel("*" * len(self.text))
#         else:
#             self.textControl.setLabel(self.text)
#
#     def getText(self):
#         return self.text
#
#
# if not hasattr(xbmcgui, "ControlEdit"):
#     xbmcgui.ControlEdit = ControlEdit
