# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Lista de vídeos descargados
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Herramientas responsables de adaptar los diferentes 
# cuadros de dialogo a una plataforma en concreto,
# en este caso Kodi.
# ------------------------------------------------------------
import xbmcgui
import xbmc

def dialog_ok(heading, line1, line2="", line3=""):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, line1, line2, line3)
    
def dialog_notification(heading, message, icon=0, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    l_icono=(xbmcgui.NOTIFICATION_INFO , xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR)
    dialog.notification (heading, message, l_icono[icon], time, sound)
    
def dialog_yesno(heading, line1, line2="", line3="", nolabel="no", yeslabel="si", autoclose=""):
    dialog = xbmcgui.Dialog()
    if autoclose:
        return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel, autoclose)
    else:
        return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)
  
    
def dialog_select(title, opciones): 
    resultado = xbmcgui.Dialog().select(title, opciones)
    if resultado ==-1: resultado = None
    return resultado
 
def dialog_progress(title, Texto):
  progreso = xbmcgui.DialogProgress()
  progreso.create(title , Texto)
  Progreso = DialogoProgreso(progreso,title)
  return Progreso   
    
def keyboard(Texto, Title="", Password=False):
    keyboard = xbmc.Keyboard(Texto, Title, Password)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return None
    
class DialogoProgreso(object):
  Progreso=""
  Titulo=""
  Closed=False
  def __init__(self, Progreso, Titulo):
    self.Progreso = Progreso
    self.Titulo = Titulo
    self.Closed = False
  
  def iscanceled(self):
    return (self.Progreso.iscanceled() or self.Closed)

  def update(self,Porcentaje, Texto):
    Linea1=" "
    Linea2=" "
    Linea3=" "
    if len(Texto.split("\n"))>0:
      Linea1= Texto.split("\n")[0]
    if len(Texto.split("\n"))>1:
      Linea2= Texto.split("\n")[1]
    if len(Texto.split("\n"))>2:
      Linea3= Texto.split("\n")[2]
    self.Progreso.update(Porcentaje,Linea1,Linea2,Linea3)

  def close(self):
    self.Progreso.close()
    self.Closed = True    