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

DEBUG = True
CHANNELNAME = "configuracion"


def mainlist(item):
    logger.info("tvalacarta.channels.configuracion mainlist")

    itemlist = []
    itemlist.append(Item(channel=CHANNELNAME, title="Preferencias", action="settings", folder=False))
    itemlist.append(Item(channel=CHANNELNAME, title="", action="", folder=False))
    itemlist.append(Item(channel="novedades", title="Ajustes de la sección 'Novedades'", action="menu_opciones", folder=True))
    itemlist.append(Item(channel="buscador", title="Ajustes del buscador global", action="opciones", folder=True))
    itemlist.append(Item(channel=CHANNELNAME, title="", action="", folder=False))
    if config.is_xbmc():
        itemlist.append(Item(channel=item.channel, action="updatebiblio",
                             title="Buscar nuevos episodios y actualizar biblioteca", folder=False))
        itemlist.append(Item(channel=item.channel, action="", title="", folder=False))
    itemlist.append(Item(channel=CHANNELNAME, title="Comprobar actualizaciones", action="check_for_updates", folder=False))

    return itemlist


def check_for_updates(item):
    from core import updater
    updater.checkforupdates()


def settings(item):
    config.open_settings()


def updatebiblio(item):
    logger.info("pelisalacarta.channels.ayuda updatebiblio")

    import library_service
    library_service.main()


