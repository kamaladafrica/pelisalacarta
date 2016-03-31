# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# XBMC Config Menu
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# ------------------------------------------------------------
import os
import sys 
import json
import inspect
import xbmc
import xbmcgui
import xbmcplugin
from core import channeltools
from core import config
from core import logger
class SettingsWindow(xbmcgui.WindowXMLDialog):

        def get_channel_settings(self):
            #Obtenemos el canal desde donde se ha echo la llamada y cargamos los settings disponibles para ese canal
            channelpath = inspect.currentframe().f_back.f_back.f_back.f_code.co_filename
            channelname = os.path.basename(channelpath).replace(".py", "")
            channelsfolder = os.path.join(config.get_runtime_path(), "channels")
            if channelsfolder in channelpath:
                # La llamada se hace desde un canal
                list_controls, dict_settings = channeltools.get_channel_controls_settings(channelname)
                self.list_controls = list_controls
                self.JSONFileData = os.path.join(config.get_data_path(), "settings_channels", channelname + "_data.json")


        def Start(self, channel=None, json_file=None,list_controls=None, values=None, title="Opciones"):
        
            self.mediapath = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media')
            self.title = title
            self.JSONFileData = None
            self.list_controls = list_controls
            self.values = values
            self.channel = channel
            self.isConfirmed = False
            
            if self.title.startswith('@') and unicode(self.title[1:]).isnumeric():
                self.title = config.get_localized_string(int(self.title[1:]))
            
            #Si no se pasan controles, intenta buscar los controles para el canal desde el que se ha llamado
            if self.list_controls is None:
              
              #Si no se indica canal, intenta detectarllo
              if self.channel is None:
                self.get_channel_settings()
              
              #Si se indica canal, lee los controles del xml
              else:
                self.list_controls, dict_settings = channeltools.get_channel_controls_settings(self.channel)
                self.JSONFileData = os.path.join(config.get_data_path(), "settings_channels", self.channel + "_data.json")
                
            #Si llegados a este punto no hay controles, devuelve un error  
            if self.list_controls is None: raise Exception("No controls loaded")
            
            #Si se indica la ruta para guardar, se usa esta
            if json_file: self.JSONFileData = json_file
            
            #Si no hay valores, leerlos del JSON
            if self.JSONFileData is not None and self.values == None:
              try:
                  self.values = json.loads(open(self.JSONFileData, "r").read())
              except:
                pass
            
            #Si sigue sin haber valores, crea un dict vacio    
            if self.values is None: self.values = {}
            
            #Muestra la ventana
            self.doModal()
            if self.isConfirmed:
              return self.values
            else:
              return {}

        def onInit(self):
            #Ponemos el título
            self.getControl(10002).setLabel(self.title)
            
            #Obtenemos las dimensiones del area de controles
            self.ContolsWidth = self.getControl(10007).getWidth() - 20
            self.ContolsHeight = self.getControl(10007).getHeight()
            self.ContolsX = self.getControl(10007).getX() + self.getControl(10001).getX() + 10
            self.ContolsY = self.getControl(10007).getY() + self.getControl(10001).getY()
            self.height_control = 35
            self.font = "font12"
            
            #Creamos un listado de controles, para tenerlos en todo momento localizados y posicionados en la ventana
            self.controls = []
            
            x = 0
            for c in self.list_controls:
                #Posicion Y para cada control
                PosY = self.ContolsY + x * self.height_control
                
                #Saltamos controles que no tengan los valores adecuados
                if not "type" in c: continue
                if not "label" in c: continue
                if c["type"] != "label" and not "id" in c: continue

                if c["type"] == "list" and not "lvalues" in c: continue
                if c["type"] == "list" and not type(c["lvalues"]) == list: continue
                if c["type"] == "list" and not len(c["lvalues"]) > 0: continue
                if c["type"] != "label" and c["id"] in [control["id"] for control in self.controls]: continue
                
                # Translation label y lvalues
                if c['label'].startswith('@') and unicode(c['label'][1:]).isnumeric():
                  c['label'] = config.get_localized_string(int(c['label'][1:]))
                if c['type'] == 'list':
                  lvalues=[]
                  for li in c['lvalues']:
                      if li.startswith('@') and unicode(li[1:]).isnumeric():
                          lvalues.append(config.get_localized_string(int(li[1:])))
                      else:
                          lvalues.append(li)
                  c['lvalues'] = lvalues
                  
                                
                #Valores por defecto en caso de que el control no disponga de ellos
                if c["type"] == "bool" and not "default" in c: c["default"] = False
                if c["type"] == "text" and not "default" in c: c["default"] = ""
                if c["type"] == "text" and not "hidden" in c: c["hidden"] = False
                if c["type"] == "list" and not "default" in c: c["default"] = 0
                if c["type"] == "label" and not "color" in c: c["color"] = "0xFF0066CC"
                if c["type"] == "label" and not "id" in c: c["id"] = None
                
                #Para simplificar el codigo pasamos los campos a veriables
                id = c["id"]
                label = c['label']
                ctype = c["type"]
                if ctype == "label": color = c["color"]
                if ctype == "list": lvalues = c["lvalues"]
                if ctype == "text": hidden = c["hidden"]
                
                #Decidimos si usar el valor por defecto o el valor guardado
                if ctype in ["bool", "text", "list"]:
                    default = c["default"]
                    if id in self.values:
                        value = self.values[id]
                    else:
                        self.values[id] = c["default"]
                        value = self.values[id]

                
                #Control "bool"
                if ctype == "bool":
                    #Creamos el control
                    control = xbmcgui.ControlRadioButton(self.ContolsX - 10, -100, self.ContolsWidth + 10, self.height_control, label=label, font=self.font,
                                                         focusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'MenuItemFO.png'),
                                                         noFocusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'MenuItemNF.png'),
                                                         focusOnTexture=os.path.join(self.mediapath, 'ChannelSettings', 'radiobutton-focus.png'),
                                                         noFocusOnTexture=os.path.join(self.mediapath, 'ChannelSettings', 'radiobutton-focus.png'),
                                                         focusOffTexture=os.path.join(self.mediapath, 'ChannelSettings', 'radiobutton-nofocus.png'),
                                                         noFocusOffTexture=os.path.join(self.mediapath, 'ChannelSettings', 'radiobutton-nofocus.png'))
                    #Lo añadimos a la ventana
                    self.addControl(control)
                    
                    #Cambiamos las propiedades
                    control.setRadioDimension(x=self.ContolsWidth + 10 - (self.height_control - 5), y=0, width=self.height_control - 5, height=self.height_control - 5)
                    control.setSelected(value)
                    control.setVisible(False)
                    
                    #Lo añadimos al listado
                    self.controls.append({"id": id, "type": ctype, "control": control, "x": self.ContolsX - 10, "y": PosY, "default": default})
                
                #Control "text"
                elif ctype == 'text':
                    #Creamos el control
                    control = xbmcgui.ControlEdit(self.ContolsX, -100, self.ContolsWidth - 5, self.height_control, label, font=self.font, isPassword=hidden,
                                                  focusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'MenuItemFO.png'),
                                                  noFocusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'MenuItemNF.png'))
                    #Lo añadimos a la ventana                             
                    self.addControl(control)
                    
                    #Cambiamos las propiedades
                    control.setVisible(False)
                    control.setLabel(label)
                    control.setText(value)
                    control.setPosition(self.ContolsX, PosY)
                    control.setWidth(self.ContolsWidth - 5)
                    control.setHeight(self.height_control)
                    
                    #Lo añadimos al listado
                    self.controls.append({"id": id, "type": ctype, "control": control, "x": self.ContolsX, "y": PosY, "default": default})
                
                #Control "list"
                elif ctype == 'list':
                    #Creamos los controles el list se forma de 3 controles
                    control = xbmcgui.ControlButton(self.ContolsX, -100, self.ContolsWidth, self.height_control, label, font=self.font, textOffsetX=0,
                                                    focusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'MenuItemFO.png'),
                                                    noFocusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'MenuItemNF.png'))
                                                    
                    label = xbmcgui.ControlLabel(self.ContolsX, -100, self.ContolsWidth - 30, self.height_control, lvalues[lvalues.index(value)], font=self.font, alignment=4 | 1)
                    
                    upBtn = xbmcgui.ControlButton(self.ContolsX + self.ContolsWidth - 25, -100, 20, 15, '',
                                                  focusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'spinUp-Focus.png'),
                                                  noFocusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'spinUp-noFocus.png'))
                    
                    downBtn = xbmcgui.ControlButton(self.ContolsX + self.ContolsWidth - 25, -100 + 15, 20, 15, '',
                                                    focusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'spinDown-Focus.png'),
                                                    noFocusTexture=os.path.join(self.mediapath, 'ChannelSettings', 'spinDown-noFocus.png'))
                                                                                                                                          
                    #Los añadimos a la ventana
                    self.addControl(control)
                    self.addControl(label)
                    self.addControl(upBtn)
                    self.addControl(downBtn)
                    
                    #Cambiamos las propiedades
                    control.setVisible(False)
                    label.setVisible(False)
                    upBtn.setVisible(False)
                    downBtn.setVisible(False)
                    
                    #Lo añadimos al listado
                    self.controls.append({"id": id, "type": ctype, "control": control, "label": label, "downBtn": downBtn, "upBtn": upBtn, "x": self.ContolsX, "y": PosY, "lvalues": c["lvalues"], "default": default})


                #Control "label"
                elif ctype == 'label':
                    #Creamos el control
                    control = xbmcgui.ControlLabel(self.ContolsX, -100, self.ContolsWidth, height=30, label=label, alignment=4, font=self.font, textColor=color)
                    
                    #Lo añadimos a la ventana
                    self.addControl(control)
                    
                    #Cambiamos las propiedades
                    control.setVisible(False)
                    
                    #Lo añadimos al listado
                    self.controls.append({"id": None, "type": ctype, "control": control, "x": self.ContolsX, "y": PosY})
                
                
                #Esto es para reposicionar el control en la ventana
                self.Scroll(1)
                
                x += 1
                
            #Ponemos el foco en el primer control   
            self.setFocus(self.controls[0]["control"])


        def MoveUp(self):
            #Subir el foco al control de arriba
            
            #Buscamos el control con el foco
            try:
                focus = self.getFocus()
            except:
                #Si ningún control tiene foco, seleccionamos el primero de la lista y salimos de la función
                control = self.controls[0]
                
                #Los label no tienen foco, si el primero es label, va saltando hasta encontrar uno que no lo sea
                while control["type"] == "label" and self.controls.index(control) < len(self.controls) - 1:
                    control = self.controls[self.controls.index(control) + 1]
                    
                self.setFocus(control["control"])
                return
                
            #Localizamos en el listado de controles el control que tiene el focus
            for x, control in enumerate(self.controls):
                if control["control"] == focus:
                    #Sube uno en la lista
                    x -= 1 if x > 0 else 0
                            
                    #Si es un label, sigue subiendo hasta llegar al primero o uno que nos sea label
                    while self.controls[x]["type"] == "label" and x > 0:
                        x -= 1
                        
                    #Si llegado aqui sigue siendo un label es que no quedan mas controles que no sean label, sale de la funcion
                    if self.controls[x]["type"] == "label": return
                    
                    #Si el control seleccionado no esta visible (esta fuera de la ventana en el scroll) sube el scroll hasta que este visible    
                    while not self.controls[x]["visible"]: self.Scroll(1)
                    
                    #Pasamos el foco al control
                    self.setFocus(self.controls[x]["control"])


        def MoveDown(self):
            #Bajar el foco al control de abajo
            
            #Buscamos el control con el foco
            try:
                focus = self.getFocus()
            except:
                #Si ningún control tiene foco, seleccionamos el primero de la lista y salimos de la función
                control = self.controls[0]
                
                #Los label no tienen foco, si el primero es label, va saltando hasta encontrar uno que no lo sea
                while control["type"] == "label" and self.controls.index(control) < len(self.controls) - 1:
                    control = self.controls[self.controls.index(control) + 1]
                    
                self.setFocus(control["control"])
                return
                
            #Localizamos en el listado de controles el control que tiene el focus
            for x, control in enumerate(self.controls):
                if control["control"] == focus:
                
                    #Baja uno en la lista
                    x += 1
                    
                    #Si es un label, sigue bajando hasta llegar al primero o uno que nos sea label    
                    while x < len(self.controls) and self.controls[x]["type"] == "label":
                        x += 1

                    #Si llegado aqui sigue siendo un label o no quedan mas controles pasa el foco los botones inferiores y sale de la función
                    if x >= len(self.controls) or self.controls[x]["type"] == "label":
                        self.setFocusId(10004)
                        return
                        
                    #Si el control seleccionado no esta visible (esta fuera de la ventana en el scroll) baja el scroll hasta que este visible      
                    while not self.controls[x]["visible"]: self.Scroll(-1)
                    
                    #Pasamos el foco al control
                    self.setFocus(self.controls[x]["control"])


        def Scroll(self,direction):
        
            #Establece los pixeles y la dirección donde se moveran los controles
            movimento = self.height_control * direction
            
            #Tope inferior, si el ultimo control es visible y se hace scroll hacia abajo, el movimiento es 0
            if movimento < 0 and self.controls[-1]["y"] + self.height_control < self.ContolsY + self.ContolsHeight:
                movimento = 0
            
            #Tope superior, si el primer control es visible y se hace scroll hacia arriba, el movimiento es 0
            if movimento > 0 and self.controls[0]["y"] == self.ContolsY:
                movimento = 0
                
            #Mueve todos los controles una posicion
            for control in self.controls:
            
                #Asigna la nueva posición en la lista de controles
                control["y"] += movimento

                #Si el control está dentro del espació visible, lo coloca en la posición y lo marca como visible
                if control["y"] > self.ContolsY - self.height_control and control["y"] + self.height_control < self.ContolsHeight + self.ContolsY:
                    if control["type"] != "list":
                        control["control"].setPosition(control["x"], control["y"])
                        control["control"].setVisible(True)
                    else:
                        control["control"].setPosition(control["x"], control["y"])
                        control["control"].setVisible(True)
                        control["label"].setPosition(control["x"], control["y"])
                        control["label"].setVisible(True)
                        control["upBtn"].setPosition(control["x"] + control["control"].getWidth() - 25, control["y"] + 3)
                        control["upBtn"].setVisible(True)
                        control["downBtn"].setPosition(control["x"] + control["control"].getWidth() - 25, control["y"] + 18)
                        control["downBtn"].setVisible(True)
                        
                    #Marca el control en la lista de controles como visible
                    control["visible"] = True
                    
                #Si el control no está dentro del espació visible lo marca como no visible    
                else:
                    if control["type"] != "list":
                        control["control"].setVisible(False)
                    else:
                        control["control"].setVisible(False)
                        control["label"].setVisible(False)
                        control["downBtn"].setVisible(False)
                        control["upBtn"].setVisible(False)
                    
                    #Marca el control en la lista de controles como no visible
                    control["visible"] = False
            
            #Calculamos la posicion y tamaño del ScrollBar
            show_controls   = [control for control in self.controls if control["visible"] == True]
            hidden_controls = [control for control in self.controls if control["visible"] == False]
            position        = self.controls.index(show_controls[0])
  
            scrollbar_height = self.getControl(10008).getHeight() - (len(hidden_controls) * 5)
            scrollbar_y = self.getControl(10008).getY() + (position * 5)
            self.getControl(10009).setPosition(self.getControl(10008).getX(), scrollbar_y)
            self.getControl(10009).setHeight(scrollbar_height)


        def onClick(self, id):
            #Valores por defecto
            if id == 10006:
                for c in self.controls:
                    if c["type"] == "text":
                        c["control"].setText(c["default"])
                        self.values[c["id"]] = c["default"]
                    if c["type"] == "bool":
                        c["control"].setSelected(c["default"])
                        self.values[c["id"]] = c["default"]
                    if c["type"] == "list":
                        c["label"].setLabel(c["default"])
                        self.values[c["id"]] = c["default"]
                        
            #Boton Cancelar y [X]
            if id == 10003 or id == 10005:
                self.close()
                
            #Boton Aceptar    
            if id == 10004:
                #Si tenemos el archivo donde guardar los ajustes, los guardamos
                if self.JSONFileData is not None:
                  open(self.JSONFileData, "w").write(json.dumps(self.values, indent=4, sort_keys=True))
                
                #Cerramos la ventana
                self.isConfirmed = True
                self.close()
            
            #Controles de ajustes, si se cambia el valor de un ajuste, cambiamos el valor guardado en el listado de controles
            #Obtenemos el control sobre el que se ha echo click
            control = self.getControl(id)
            
            #Lo buscamos en el listado de controles
            for cont in self.controls:
            
                #Si el control es un "downBtn" o "upBtn" son los botones del "list"
                #en este caso cambiamos el valor del list
                if cont["type"] == "list" and (cont["downBtn"] == control or cont["upBtn"] == control):
                
                    #Para bajar una posicion
                    if cont["downBtn"] == control:
                        index = cont["lvalues"].index(cont["label"].getLabel())
                        if index > 0:
                            cont["label"].setLabel(cont["lvalues"][index - 1])
                            
                    #Para subir una posicion
                    elif cont["upBtn"] == control:
                        index = cont["lvalues"].index(cont["label"].getLabel())
                        if index < len(cont["lvalues"]) - 1:
                            cont["label"].setLabel(cont["lvalues"][index + 1])
                    
                    #Guardamos el nuevo valor en el listado de controles
                    self.values[cont["id"]] = cont["label"].getLabel()
                    
                #Si esl control es un "bool", guardamos el nuevo valor True/False    
                if cont["type"] == "bool" and cont["control"] == control: self.values[cont["id"]] = bool(cont["control"].isSelected())
                
                #Si esl control es un "text", guardamos el nuevo valor
                if cont["type"] == "text" and cont["control"] == control: self.values[cont["id"]] = cont["control"].getText()

        def onAction(self, action):
            #Accion 1: Flecha derecha
            if action == 1:
                #Obtenemos el foco
                focus = self.getFocusId()
                
                #Si el foco no está en ninguno de los tres botones inferiores, y esta en un "list" cambiamos el valor
                if not focus in [10004, 10005, 10006]:
                    control = self.getFocus()
                    for cont in self.controls:
                        if cont["type"] == "list" and cont["control"] == control:
                            index = cont["lvalues"].index(cont["label"].getLabel())
                            if index > 0:
                                cont["label"].setLabel(cont["lvalues"][index - 1])
                                
                            #Guardamos el nuevo valor en el listado de controles
                            self.values[cont["id"]] = cont["label"].getLabel()
                    
                #Si el foco está en alguno de los tres botones inferiores, movemos al siguiente
                else:
                    if focus == 10006: self.setFocusId(10005)
                    if focus == 10005: self.setFocusId(10004)
                    
            #Accion 1: Flecha izquierda
            if action == 2:
                #Obtenemos el foco
                focus = self.getFocusId()
                
                #Si el foco no está en ninguno de los tres botones inferiores, y esta en un "list" cambiamos el valor
                if not focus in [10004, 10005, 10006]:
                    control = self.getFocus()
                    for cont in self.controls:
                        if cont["type"] == "list" and cont["control"] == control:
                            index = cont["lvalues"].index(cont["label"].getLabel())
                            if index < len(cont["lvalues"]) - 1:
                                cont["label"].setLabel(cont["lvalues"][index + 1])
                                
                            #Guardamos el nuevo valor en el listado de controles
                            self.values[cont["id"]] = cont["label"].getLabel()
                            
                #Si el foco está en alguno de los tres botones inferiores, movemos al siguiente
                else:
                    if focus == 10004: self.setFocusId(10005)
                    if focus == 10005: self.setFocusId(10006)
                    
            #Accion 4: Flecha abajo
            if action == 4:
                #Obtenemos el foco
                focus = self.getFocusId()
                
                #Si el foco no está en ninguno de los tres botones inferiores, bajamos el foco en los controles de ajustes
                if not focus in [10004, 10005, 10006]:
                    self.MoveDown()
            
            #Accion 4: Flecha arriba
            if action == 3:
                #Obtenemos el foco
                focus = self.getFocusId()
                
                 #Si el foco no está en ninguno de los tres botones inferiores, subimos el foco en los controles de ajustes
                if not focus in [10004, 10005, 10006]:
                    self.MoveUp()
                
                #Si el foco está en alguno de los tres botones inferiores, ponemos el foco en el ultimo ajuste.
                else:
                    self.setFocus(self.controls[-1]["control"])
                    
            #Accion 104: Scroll arriba
            if action == 104:
                self.Scroll(1)
            
            #Accion 105: Scroll abajo
            if action == 105:
                self.Scroll(-1)
                
            #Accion 10: Back
            if action == 10:
                self.close()