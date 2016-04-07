# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# platformtools
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Herramientas responsables de adaptar los diferentes 
# cuadros de dialogo a una plataforma en concreto,
# en este caso Kodi.
# version 1.3
# ------------------------------------------------------------
import xbmcgui
import xbmc
import os
from core import config

def dialog_ok(heading, line1, line2="", line3=""):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, line1, line2, line3)
    
def dialog_notification(heading, message, icon=0, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    l_icono=(xbmcgui.NOTIFICATION_INFO , xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR)
    dialog.notification (heading, message, l_icono[icon], time, sound)

def dialog_yesno(heading, line1, line2="", line3="", nolabel="No", yeslabel="Si", autoclose=""):
    dialog = xbmcgui.Dialog()
    if autoclose:
        return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel, autoclose)
    else:
        return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)
  
def dialog_select(heading, list): 
    return xbmcgui.Dialog().select(heading, list)
    
def dialog_progress(heading, line1, line2="", line3=""):
    dialog = xbmcgui.DialogProgress()
    dialog.create(heading, line1, line2, line3)
    return dialog

def dialog_progress_bg(heading, message=""):
    dialog = xbmcgui.DialogProgressBG()
    dialog.create(heading, message)
    return dialog

def dialog_input(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return None

def dialog_numeric(type, heading, default=""):
    dialog = xbmcgui.Dialog()
    dialog.numeric(type, heading, default)
    return dialog
        
def itemlist_refresh():
    xbmc.executebuiltin("Container.Refresh")

def itemlist_update(item):
    xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")

def render_items(itemlist, parentitem):
    #Por implementar (traer de xbmctools)
    pass
    
def is_playing():
    return xbmc.Player().isPlaying()

def play_video(item):
    #Por implementar (traer de xbmctools)
    pass
    
def show_channel_settings(list_controls=None, dict_values=None, caption="", cb=None, item=None):
    from xbmc_config_menu import SettingsWindow
    return SettingsWindow("ChannelSettings.xml", config.get_runtime_path()).Start(list_controls=list_controls, values=dict_values, title=caption, cb=cb, item=item)
