# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------

from core import logger
from core.item import Item


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="submenu1", title="Menu 1"))
    itemlist.append(Item(channel=item.channel, action="submenu2", title="Menu 2"))

    return itemlist

def submenu1(item):

    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="submenu1_action1", title="Submenu 1.1"))
    itemlist.append(Item(channel=item.channel, action="submenu1_action2", title="Submenu 1.2"))

    return itemlist

def submenu2(item):

    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="submenu2_action_1", title="Submenu 2.1"))
    itemlist.append(Item(channel=item.channel, action="submenu2_action_2", title="Submenu 2.2"))

    return itemlist