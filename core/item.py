# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta 4
# Copyright 2015 tvalacarta@gmail.com
#
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
#------------------------------------------------------------
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
#------------------------------------------------------------

import json
import base64
import urllib
import copy

class Item(object):  
    
    def __contains__(self, m):
        return m in self.__dict__
        
    def __init__(self,  **kwargs):     
        #Campos por defecto de la clase Item
        kwargs.setdefault("channel", "")            #Canal en el que se ejecuta
        kwargs.setdefault("action", "")             #funcion que ejecutará en el canal
        kwargs.setdefault("title", "")              #Nombre para mostrar y nombre de la pelicula
        kwargs.setdefault("fulltitle", "")          #Titulo de la pelicula en caso de ser distinto al del campo "title"
        kwargs.setdefault("show", "")               #Nombre de la serie
        kwargs.setdefault("plot", "")               #Descripción
        kwargs.setdefault("url", "")                #Url
        kwargs.setdefault("thumbnail", "")          #Imagen
        kwargs.setdefault("fanart", "")             #Imagen de Fondo
        kwargs.setdefault("password", "")           #Password del video

        kwargs.setdefault("folder", True)           #Carpeta o vídeo
        kwargs.setdefault("server", "")             #Servidor que contiene el vídeo
        kwargs.setdefault("extra", "")              #Datos extra
        
        kwargs.setdefault("language", "")           #Idioma del contenido
        kwargs.setdefault("context", "")            #Items para el Menú Contextual
        kwargs.setdefault("subtitle", "")           #Subtitulos
        kwargs.setdefault("duration", 0)            #Duracion de la pelicula
        kwargs.setdefault("category", "")           #Categoria de la pelicula
        
        kwargs.setdefault("infoLabels", dict())     #Diccionario con informacion extra sobre la pelicula o serie

        kwargs.setdefault("viewmode", "list")       #Modo de ventana

        kwargs.setdefault("hasContentDetails", "false")

        kwargs.setdefault("contentChannel", "list") # En qué canal estaba el contenido
        kwargs.setdefault("contentTitle","")
        kwargs.setdefault("contentThumbnail","")
        kwargs.setdefault("contentPlot","")
        kwargs.setdefault("contentType","")
        kwargs.setdefault("contentSerieName","")
        kwargs.setdefault("contentSeason","")
        kwargs.setdefault("contentEpisodeNumber","")
        kwargs.setdefault("contentEpisodeTitle","")

        if kwargs.has_key("parentContent") and kwargs["parentContent"] is not None:

            print "Tiene parentContent: "+repr(kwargs["parentContent"])
            parentContent = kwargs["parentContent"]
            # Removed from dictionary, should not be included
            kwargs.pop("parentContent",None)

        else:
            parentContent = None

        self.__dict__.update(kwargs)
        self.__dict__ = self.toutf8(self.__dict__)

        if parentContent is not None:
            self.contentChannel = parentContent.contentChannel;
            self.contentTitle = parentContent.contentTitle;
            self.contentThumbnail = parentContent.contentThumbnail;
            self.contentPlot = parentContent.contentPlot;

            self.hasContentDetails = parentContent.hasContentDetails;
            self.contentType = parentContent.contentType;
            self.contentSerieName = parentContent.contentSerieName;
            self.contentSeason = parentContent.contentSeason;
            self.contentEpisodeNumber = parentContent.contentEpisodeNumber;
            self.contentEpisodeTitle = parentContent.contentEpisodeTitle;
    
       
    def tostring(self):
        '''
        Genera una cadena de texto con los datos del item para el log
        Uso: logger.info(item.tostring())
        '''
        return ", ".join([var + "=["+str(self.__dict__[var])+"]" for var in sorted(self.__dict__)])        
        

    def tourl(self):
        '''
        Genera una cadena de texto con los datos del item para crear una url, para volver generar el Item usar item.fromurl()
        Uso: url = item.tourl()
        '''
        return urllib.quote(base64.b64encode(json.dumps(self.__dict__)))
              

    def fromurl(self,url): 
        '''
        Genera un item a partir de la cadena de texto creada por la funcion tourl()
        Uso: item.fromurl("cadena")
        '''
        STRItem = base64.b64decode(urllib.unquote(url))
        JSONItem = json.loads(STRItem,object_hook=self.toutf8)
        self.__dict__.update(JSONItem)
        return self


    def tojson(self, path=""):
        '''
        Crea un JSON a partir del item, para guardar archivos de favoritos, lista de descargas, etc...
        Si se especifica un path, te lo guarda en la ruta especificada, si no, devuelve la cadena json
        Usos: item.tojson(path="ruta\archivo\json.json")
              file.write(item.tojson())
        '''      
        if path:
          open(path,"wb").write(json.dumps(self.__dict__, indent=4, sort_keys=True))
        else:
          return json.dumps(self.__dict__, indent=4, sort_keys=True)
              

    def fromjson(self,STRItem={}, path=""): 
        '''
        Genera un item a partir de un archivo JSON
        Si se especifica un path, lee directamente el archivo, si no, lee la cadena de texto pasada.
        Usos: item = Item().fromjson(path="ruta\archivo\json.json")
              item = Item().fromjson("Cadena de texto json")
        '''
        if path:
          if os.path.exists(path):
            STRItem = open(path,"rb").read()
          else:
            STRItem = {}
            
        JSONItem = json.loads(STRItem,object_hook=self.toutf8)
        self.__dict__.update(JSONItem)
        return self
          
        
    def clone(self,**kwargs):
        '''
        Genera un nuevo item clonando el item actual
        Usos: NuevoItem = item.clone()
              NuevoItem = item.clone(title="Nuevo Titulo", action = "Nueva Accion")
        '''
        newitem = copy.deepcopy(self)
        newitem.__dict__.update(kwargs)
        newitem.__dict__ = newitem.toutf8(newitem.__dict__)
        return newitem
      

    def toutf8(self, *args):
        if len(args)>0:  value = args[0]
        else: value = self.__dict__
        
        if type(value)== unicode:
            return value.encode("utf8")
          
        elif type(value)== str:
            return unicode(value,"utf8", "ignore").encode("utf8")
          
        elif type(value)== list:
            for x, key in enumerate(value):
                value[x] = self.toutf8(value[x])
            return value
          
        elif type(value)== dict:
            newdct = {}
            for key in value:
                if type(key) == unicode:
                    key = key.encode("utf8")
                  
                newdct[key] = self.toutf8(value[key])

            if len(args)>0: return newdct
        
        else:
            return value

    def get_InfoLabels(self, reload=False, idioma_busqueda='es'):
        # reload= True hace una busqueda en tmdb
        
        # Fijar valores por defecto
        if not self.infoLabels.has_key('year'): self.infoLabels['year'] = ''
        if not self.infoLabels.has_key('IMDBNumber'): self.infoLabels['IMDBNumber'] = ''
        if not self.infoLabels.has_key('code'): self.infoLabels['code'] = ''
        if not self.infoLabels.has_key('imdb_id'): self.infoLabels['imdb_id'] = ''
        if not self.infoLabels.has_key('plot'):self.infoLabels['plot'] = self.plot if self.plot !='' else self.contentPlot
        if not self.infoLabels.has_key('genre'):self.infoLabels['genre'] = self.category
        self.infoLabels['duration'] = self.duration
        self.infoLabels['AudioLanguage'] = self.language
        titulo = self.fulltitle if self.fulltitle !='' else (self.contentTitle if self.contentTitle !='' else self.title)
        if not self.infoLabels.has_key('title'): self.infoLabels['title'] = titulo
        tvshowtitle = self.show if self.show !='' else self.contentSerieName
        tipo = 'tv' if tvshowtitle !='' else 'movie'
        
        if reload: 
            from core.tmdb import Tmdb
            otmdb = None
            sources = ("tvdb_id","imdb_id","freebase_mid","freebase_id","tvrage_id") if tipo == 'tv' else ("imdb_id")
            if self.infoLabels['IMDBNumber'] or self.infoLabels['code'] or self.infoLabels['imdb_id']:
                if self.infoLabels['IMDBNumber']:
                    self.infoLabels['code'] ==  self.infoLabels['IMDBNumber']
                    self.infoLabels['imdb_id'] == self.infoLabels['IMDBNumber']
                elif self.infoLabels['code']:
                    self.infoLabels['IMDBNumber'] ==  self.infoLabels['code']
                    self.infoLabels['imdb_id'] == self.infoLabels['code']
                else:     
                    self.infoLabels['code'] == self.infoLabels['imdb_id']
                    self.infoLabels['IMDBNumber'] == self.infoLabels['imdb_id']     
                #buscar con imdb code
                otmdb= Tmdb(self.infoLabels['imdb_id'], "imdb_id", tipo, idioma_busqueda= idioma_busqueda)
            
            elif (titulo and self.infoLabels['year']):
                #buscar con titulo y nombre
                otmdb= Tmdb(texto_buscado= titulo,tipo= tipo, year= str(self.infoLabels['year']), idioma_busqueda= idioma_busqueda)  
                
            elif tipo == 'tv': #buscar con otros codigos
                if self.infoLabels['tvdb_id']:
                    otmdb= Tmdb(self.infoLabels['tvdb_id'], "tvdb_id", tipo, idioma_busqueda= idioma_busqueda)
                elif self.infoLabels['freebase_mid']:
                    otmdb= Tmdb(self.infoLabels['freebase_mid'], "freebase_mid", tipo, idioma_busqueda= idioma_busqueda) 
                elif self.infoLabels['freebase_id']:
                    otmdb= Tmdb(self.infoLabels['freebase_id'], "freebase_id", tipo, idioma_busqueda= idioma_busqueda) 
                elif self.infoLabels['tvrage_id']:
                    otmdb= Tmdb(self.infoLabels['tvrage_id'], "tvrage_id", tipo, idioma_busqueda= idioma_busqueda) 
            
   
            if otmdb == None: #No se puede hacer la busqueda en tmdb
                reload = False
            elif not otmdb.get_id(): #La busqueda no ha dado resultado
                reload = False
            else: #La busqueda ha encontrado un resultado valido
                
                #self.infoLabels['tvshowtitle'] 
                for k,v in otmdb.result.items():
                    if k == 'overview':
                        self.infoLabels['plot'] = otmdb.get_sinopsis()
                    elif k == 'release_date' and v!='':
                        self.infoLabels['year'] = int(v[:4])
                        #self.infoLabels['aired'] = '2005-3-25'
                        #self.infoLabels['premiered'] = '2005-3-25' 
                    elif k == 'original_title':
                        self.infoLabels['originaltitle'] = v
                    elif k == 'vote_average' and v !='':
                        self.infoLabels['rating'] = float(v)
                    elif k == 'vote_count':
                        self.infoLabels['votes'] = v
                    elif k == 'poster_path' and v !='':
                        self.thumbnail = 'http://image.tmdb.org/t/p/original' + v
                    elif k == 'backdrop_path' and v !='':
                        self.fanart = 'http://image.tmdb.org/t/p/original' + v
                    elif k == 'imdb_id':
                        self.infoLabels['IMDBNumber'] = v
                        self.infoLabels['code'] = v
                    elif k == 'genres':
                        self.infoLabels['genre'] = otmdb.get_generos()
                    elif type(v) == str:
                        self.infoLabels[k] = v
                    
                    
        if not reload:
            self.infoLabels['tvshowtitle'] = tvshowtitle
            if self.contentSeason !='': self.infoLabels['season'] = int(self.contentSeason)
            if self.contentEpisodeNumber !='': self.infoLabels['episode'] = int(self.contentEpisodeNumber)
            if self.contentEpisodeTitle !='': self.infoLabels['episodeName'] = self.contentEpisodeTitle
             

             
        return self.infoLabels    

         
           