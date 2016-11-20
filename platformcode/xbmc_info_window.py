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

import inspect
import os
import re

import xbmcgui

from core.tmdb import Tmdb
from core.item import Item, InfoLabels
from core import logger


class InfoWindow(xbmcgui.WindowXMLDialog):
    otmdb = None

    item_title = ""
    item_serie = ""
    item_temporada = 0
    item_episodio = 0
    result = {}

    @staticmethod
    def get_language(lng):
        # Cambiamos el formato del Idioma
        languages = {
            'aa': 'Afar', 'ab': 'Abkhazian', 'af': 'Afrikaans', 'ak': 'Akan', 'sq': 'Albanian', 'am': 'Amharic',
            'ar': 'Arabic', 'an': 'Aragonese', 'as': 'Assamese', 'av': 'Avaric', 'ae': 'Avestan',
            'ay': 'Aymara', 'az': 'Azerbaijani', 'ba': 'Bashkir', 'bm': 'Bambara', 'eu': 'Basque',
            'be': 'Belarusian', 'bn': 'Bengali', 'bh': 'Bihari languages', 'bi': 'Bislama',
            'bo': 'Tibetan', 'bs': 'Bosnian', 'br': 'Breton', 'bg': 'Bulgarian', 'my': 'Burmese',
            'ca': 'Catalan; Valencian', 'cs': 'Czech', 'ch': 'Chamorro', 'ce': 'Chechen', 'zh': 'Chinese',
            'cu': 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic',
            'cv': 'Chuvash', 'kw': 'Cornish', 'co': 'Corsican', 'cr': 'Cree', 'cy': 'Welsh',
            'da': 'Danish', 'de': 'German', 'dv': 'Divehi; Dhivehi; Maldivian', 'nl': 'Dutch; Flemish',
            'dz': 'Dzongkha', 'en': 'English', 'eo': 'Esperanto',
            'et': 'Estonian', 'ee': 'Ewe', 'fo': 'Faroese', 'fa': 'Persian', 'fj': 'Fijian',
            'fi': 'Finnish', 'fr': 'French', 'fy': 'Western Frisian', 'ff': 'Fulah',
            'Ga': 'Georgian', 'gd': 'Gaelic; Scottish Gaelic', 'ga': 'Irish', 'gl': 'Galician',
            'gv': 'Manx', 'el': 'Greek, Modern (1453-)', 'gn': 'Guarani', 'gu': 'Gujarati',
            'ht': 'Haitian; Haitian Creole', 'ha': 'Hausa', 'he': 'Hebrew', 'hz': 'Herero', 'hi': 'Hindi',
            'ho': 'Hiri Motu', 'hr': 'Croatian', 'hu': 'Hungarian', 'hy': 'Armenian', 'ig': 'Igbo',
            'is': 'Icelandic', 'io': 'Ido', 'ii': 'Sichuan Yi; Nuosu', 'iu': 'Inuktitut',
            'ie': 'Interlingue; Occidental', 'ia': 'Interlingua (International Auxiliary Language Association)',
            'id': 'Indonesian', 'ik': 'Inupiaq', 'it': 'Italian', 'jv': 'Javanese',
            'ja': 'Japanese', 'kl': 'Kalaallisut; Greenlandic', 'kn': 'Kannada', 'ks': 'Kashmiri',
            'ka': 'Georgian', 'kr': 'Kanuri', 'kk': 'Kazakh', 'km': 'Central Khmer', 'ki': 'Kikuyu; Gikuyu',
            'rw': 'Kinyarwanda', 'ky': 'Kirghiz; Kyrgyz', 'kv': 'Komi', 'kg': 'Kongo', 'ko': 'Korean',
            'kj': 'Kuanyama; Kwanyama', 'ku': 'Kurdish', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian',
            'li': 'Limburgan; Limburger; Limburgish', 'ln': 'Lingala', 'lt': 'Lithuanian',
            'lb': 'Luxembourgish; Letzeburgesch', 'lu': 'Luba-Katanga', 'lg': 'Ganda', 'mk': 'Macedonian',
            'mh': 'Marshallese', 'ml': 'Malayalam', 'mi': 'Maori', 'mr': 'Marathi', 'ms': 'Malay', 'Mi': 'Micmac',
            'mg': 'Malagasy', 'mt': 'Maltese', 'mn': 'Mongolian', 'na': 'Nauru',
            'nv': 'Navajo; Navaho', 'nr': 'Ndebele, South; South Ndebele', 'nd': 'Ndebele, North; North Ndebele',
            'ng': 'Ndonga', 'ne': 'Nepali', 'nn': 'Norwegian Nynorsk; Nynorsk, Norwegian',
            'nb': 'Bokmål, Norwegian; Norwegian Bokmål', 'no': 'Norwegian', 'oc': 'Occitan (post 1500)',
            'oj': 'Ojibwa', 'or': 'Oriya', 'om': 'Oromo', 'os': 'Ossetian; Ossetic', 'pa': 'Panjabi; Punjabi',
            'pi': 'Pali', 'pl': 'Polish', 'pt': 'Portuguese', 'ps': 'Pushto; Pashto', 'qu': 'Quechua',
            'ro': 'Romanian; Moldavian; Moldovan', 'rn': 'Rundi', 'ru': 'Russian', 'sg': 'Sango', 'rm': 'Romansh',
            'sa': 'Sanskrit', 'si': 'Sinhala; Sinhalese', 'sk': 'Slovak', 'sl': 'Slovenian', 'se': 'Northern Sami',
            'sm': 'Samoan', 'sn': 'Shona', 'sd': 'Sindhi', 'so': 'Somali', 'st': 'Sotho, Southern', 'es': 'Spanish',
            'sc': 'Sardinian', 'sr': 'Serbian', 'ss': 'Swati', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish',
            'ty': 'Tahitian', 'ta': 'Tamil', 'tt': 'Tatar', 'te': 'Telugu', 'tg': 'Tajik', 'tl': 'Tagalog',
            'th': 'Thai', 'ti': 'Tigrinya', 'to': 'Tonga (Tonga Islands)', 'tn': 'Tswana', 'ts': 'Tsonga',
            'tk': 'Turkmen', 'tr': 'Turkish', 'tw': 'Twi', 'ug': 'Uighur; Uyghur', 'uk': 'Ukrainian',
            'ur': 'Urdu', 'uz': 'Uzbek', 've': 'Venda', 'vi': 'Vietnamese', 'vo': 'Volapük',
            'wa': 'Walloon', 'wo': 'Wolof', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'za': 'Zhuang; Chuang',
            'zu': 'Zulu'}

        return languages.get(lng, lng)

    @staticmethod
    def get_date(date):
        # Cambiamos el formato de la fecha
        if date:
            return date.split("-")[2] + "/" + date.split("-")[1] + "/" + date.split("-")[0]
        else:
            return "N/A"

    def get_episode_from_title(self, item):
        # Patron para temporada y episodio "1x01"
        pattern = re.compile("([0-9]+)[ ]*[x|X][ ]*([0-9]+)")

        # Busca en title
        matches = pattern.findall(item.title)
        if len(matches):
            self.item_temporada = matches[0][0]
            self.item_episodio = matches[0][1]

        # Busca en fulltitle
        matches = pattern.findall(item.fulltitle)
        if len(matches):
            self.item_temporada = matches[0][0]
            self.item_episodio = matches[0][1]

        # Busca en contentTitle
        matches = pattern.findall(item.contentTitle)
        if len(matches):
            self.item_temporada = matches[0][0]
            self.item_episodio = matches[0][1]

    def get_item_info(self, item):
        # Recogemos los parametros del Item que nos interesan:
        self.item_title = item.title
        if item.fulltitle:
            self.item_title = item.fulltitle
        if item.contentTitle:
            self.item_title = item.contentTitle

        if item.show:
            self.item_serie = item.show
        if item.contentSerieName:
            self.item_serie = item.contentSerieName

        if item.contentSeason:
            self.item_temporada = item.contentSeason
        if item.contentEpisodeNumber:
            self.item_episodio = item.contentEpisodeNumber

        # i no existen contentepisodeNumber o contentSeason intenta sacarlo del titulo
        if not self.item_episodio or not self.item_temporada:
            self.get_episode_from_title(item)


    def get_tmdb_movie_data(self, text):
        # Buscamos la pelicula si no lo esta ya
        if not self.otmdb:
            self.otmdb = Tmdb(texto_buscado=text, idioma_busqueda="es", tipo="movie")

        # Si no hay resultados salimos
        if not self.otmdb.get_id():
            return False

        # Informacion de la pelicula
        infoLabels = self.otmdb.get_infoLabels()
        infoLabels["mediatype"] = "movie"
        infoLabels["language"] = self.get_language(infoLabels["original_language"])
        infoLabels["puntuacion"] = str(infoLabels["rating"]) + "/10 (" + str(infoLabels["votes"]) + ")"

        self.result = infoLabels

        return True

    def get_tmdb_tv_data(self, text):
        # Buscamos la serie si no esta cargada
        if not self.otmdb:
            self.otmdb = Tmdb(texto_buscado=text, idioma_busqueda="es", tipo="tv")

        # Si no hay resultados salimos
        if not self.otmdb.get_id():
            return False

        # informacion generica de la serie
        infoLabels = self.otmdb.get_infoLabels()
        infoLabels["mediatype"] = "tvshow"
        infoLabels["language"] = self.get_language(infoLabels["original_language"])
        infoLabels["puntuacion"] = str(infoLabels["rating"]) + "/10 (" + str(infoLabels["votes"]) + ")"

        self.result = infoLabels

        # Si tenemos informacion de temporada
        if self.item_temporada:
            if not self.result["seasons"]:
                self.otmdb = Tmdb(id_Tmdb=infoLabels['tmdb_id'], idioma_busqueda="es", tipo="tv")
                #logger.debug(str(self.otmdb.get_infoLabels()))

                self.result["seasons"] = str(self.otmdb.result.get("number_of_seasons", 0))

            if self.item_temporada > self.result["seasons"]:
                self.item_temporada = self.result["season_count"]

            if self.item_episodio > self.otmdb.result.get("seasons")[self.item_temporada-1]["episode_count"]:
                self.item_episodio = self.otmdb.result.get("seasons")[self.item_temporada]["episode_count"]

            # Solicitamos información del episodio concreto
            episode_info = self.otmdb.get_episodio(self.item_temporada, self.item_episodio)

            # informacion de la temporada
            self.result["season"] = str(self.item_temporada)
            self.result["temporada_nombre"] = episode_info.get("temporada_nombre", "N/A")
            self.result["episodes"] = str(episode_info.get('temporada_num_episodios', "N/A"))
            if episode_info.get("temporada_poster"):
                self.result["thumbnail"] = episode_info.get("temporada_poster")
            if episode_info.get("temporada_sinopsis"):
                self.result["plot"] = episode_info.get("temporada_sinopsis")

            # Si tenemos numero de episodio:
            if self.item_episodio:
                # informacion del episodio
                self.result["episode"] = str(self.item_episodio)
                self.result["episode_title"] = episode_info.get("episodio_titulo", "N/A")
                self.result["date"] = self.get_date(self.otmdb.temporada[self.item_temporada]["episodes"][self.item_episodio-1].get("air_date"))
                if episode_info.get("episodio_imagen"):
                    self.result["fanart"] = episode_info.get("episodio_imagen")
                if episode_info.get("episodio_sinopsis"):
                    self.result["plot"] = episode_info.get("episodio_sinopsis")

        return True

    def get_tmdb_data(self, data_in):
        self.otmdb = None
        #logger.debug(str(data_in))

        if self.listData:
            infoLabels = InfoLabels()

            # Datos comunes a todos los listados
            infoLabels = Tmdb().get_infoLabels(infoLabels=infoLabels, origen=data_in)
            if "original_language" in infoLabels:
                infoLabels["language"] = self.get_language(infoLabels["original_language"])
            if "vote_average" in data_in and "vote_count" in data_in:
                infoLabels["puntuacion"] = str(data_in["vote_average"]) + "/10 (" + str(data_in["vote_count"]) + ")"

            self.from_tmdb = False
            self.result = infoLabels

        else:
            if isinstance(data_in,Item):
                self.from_tmdb = True
                self.get_item_info(data_in)

                # Modo Pelicula
                if not self.item_serie:
                    encontrado = self.get_tmdb_movie_data(self.item_title)
                    if not encontrado:
                        encontrado = self.get_tmdb_tv_data(self.item_title)

                else:
                    encontrado = self.get_tmdb_tv_data(self.item_serie)
                    if not encontrado:
                        encontrado = self.get_tmdb_movie_data(self.item_serie)

            if isinstance(data_in,dict):
                self.from_tmdb = False
                self.result = InfoLabels(data_in)

        #logger.debug(str(self.result))

    def Start(self, data, caption="Información del vídeo", callback=None, item=None):
        # Capturamos los parametros
        self.caption = caption
        self.callback = callback
        self.item = item
        self.indexList = -1
        self.listData = None
        self.return_value = None

        # Obtenemos el canal desde donde se ha echo la llamada y cargamos los settings disponibles para ese canal
        channelpath = inspect.currentframe().f_back.f_back.f_code.co_filename
        self.channel = os.path.basename(channelpath).replace(".py", "")
        logger.debug(data)
        if type(data) == list:
            self.listData = data
            self.indexList = 0
            data = self.listData[self.indexList]

        self.get_tmdb_data(data)

        # Muestra la ventana
        self.doModal()
        return self.return_value

    def onInit(self):
        if xbmcgui.__version__ == "1.2":
          self.setCoordinateResolution(1)
        else:
          self.setCoordinateResolution(5)
          
        # Ponemos el foco en el boton de cerrar [X]
        self.setFocus(self.getControl(10003))

        # Ponemos el título y las imagenes
        self.getControl(10002).setLabel(self.caption)
        self.getControl(10004).setImage(self.result.get("fanart", ""))
        self.getControl(10005).setImage(self.result.get("thumbnail", "images/img_no_disponible.png"))

        # Cargamos los datos para el formato pelicula
        if self.result.get("mediatype", "movie") == "movie":
            self.getControl(10006).setLabel("Titulo:")
            self.getControl(10007).setLabel(self.result.get("title", "N/A"))
            self.getControl(10008).setLabel("Titulo Original:")
            self.getControl(10009).setLabel(self.result.get("originaltitle", "N/A"))
            self.getControl(100010).setLabel("Idioma original:")
            self.getControl(100011).setLabel(self.result.get("language", "N/A"))
            self.getControl(100012).setLabel("Puntuacion:")
            self.getControl(100013).setLabel(self.result.get("puntuacion", "N/A"))
            self.getControl(100014).setLabel("Lanzamiento:")
            self.getControl(100015).setLabel(self.result.get("release_date", "N/A"))
            self.getControl(100016).setLabel("Generos:")
            self.getControl(100017).setLabel(self.result.get("genre", "N/A"))

        # Cargamos los datos para el formato serie
        else:
            self.getControl(10006).setLabel("Serie:")
            self.getControl(10007).setLabel(self.result.get("title", "N/A"))
            self.getControl(10008).setLabel("Idioma original:")
            self.getControl(10009).setLabel(self.result.get("language", "N/A"))
            self.getControl(100010).setLabel("Puntuacion:")
            self.getControl(100011).setLabel(self.result.get("puntuacion", "N/A"))
            self.getControl(100012).setLabel("Generos:")
            self.getControl(100013).setLabel(self.result.get("genre", "N/A"))

            if self.result.get("season"):
                self.getControl(100014).setLabel("Titulo temporada:")
                self.getControl(100015).setLabel(self.result.get("temporada_nombre", "N/A"))
                self.getControl(100016).setLabel("Temporada:")
                self.getControl(100017).setLabel(self.result.get("season", "N/A") + " de " +
                                                 self.result.get("seasons", "N/A"))
            if self.result.get("episode"):
                self.getControl(100014).setLabel("Titulo:")
                self.getControl(100015).setLabel(self.result.get("episode_title", "N/A"))
                self.getControl(100018).setLabel("Episodio:")
                self.getControl(100019).setLabel(self.result.get("episode", "N/A") + " de " +
                                                 self.result.get("episodes", "N/A"))
                self.getControl(100020).setLabel("Emision:")
                self.getControl(100021).setLabel(self.result.get("date", "N/A"))

        # Sinopsis
        if self.result['plot']:
            self.getControl(100022).setLabel("Sinopsis:")
            self.getControl(100023).setText(self.result.get("plot", "N/A"))
        else:
            self.getControl(100022).setLabel("")
            self.getControl(100023).setText("")

        # Cargamos los botones si es necesario
        self.getControl(10024).setVisible(self.indexList > -1) # Grupo de botones
        self.getControl(10025).setEnabled(self.indexList > 0) #Anterior
        if self.listData:
            m = len(self.listData)
        else:
             m =1
        self.getControl(10026).setEnabled(self.indexList + 1 != m)  # Siguiente
        self.getControl(100029).setLabel("(%s/%s)" %(self.indexList + 1, m)) # x/m

        # Ponemos el foco en el botón "Anterior",
        # si estuviera desactivado iria el foco al boton "Siguiente" y pasara lo mismo al botón "Cancelar"
        self.setFocus(self.getControl(10024))


    def onClick(self, id):
        logger.info("pelisalacarta.platformcode.xbmc_info_window onClick id="+repr(id))
        # Boton Cancelar y [X]
        if id == 10003 or id == 10027:
            self.close()

        # Boton Anterior
        if id == 10025 and self.indexList > 0:
            self.indexList -= 1
            self.get_tmdb_data(self.listData[self.indexList])
            self.onInit()

        # Boton Siguiente
        if id == 10026 and self.indexList < len(self.listData) - 1:
            self.indexList += 1
            self.get_tmdb_data(self.listData[self.indexList])
            self.onInit()

        # Boton Aceptar, Cancelar y [X]
        if id == 10028 or id == 10003 or id == 10027:
            self.close()
            cb_channel = None

            if self.callback:
                try:
                    cb_channel = __import__('core.%s' % self.channel, None, None, ["core.%s" % self.channel])
                except ImportError:
                    logger.error('Imposible importar %s' % self.channel)

            if id == 10028:  # Boton Aceptar
                if cb_channel:
                    self.return_value = getattr(cb_channel, self.callback)(self.item, self.listData[self.indexList])
                else:
                    self.return_value = self.result

            else:  # Boton Cancelar y [X]
                if cb_channel:
                    self.return_value = getattr(cb_channel, self.callback)(self.item, None)
                else:
                    self.return_value = None


    def onFocus(self, id):
      pass
      
    def onAction(self, action):
        logger.info("pelisalacarta.platformcode.xbmc_info_window onAction action="+repr(action.getId()))
        action = action.getId()

        # Accion 1: Flecha izquierda
        if action == 1:
            # Obtenemos el foco
            focus = self.getFocusId()

            # botón Aceptar
            if focus == 10028:
                self.setFocus(self.getControl(10027))
            # botón Cancelar
            elif focus == 10027:
                if self.indexList + 1 != len(self.listData):
                    # vamos al botón Siguiente
                    self.setFocus(self.getControl(10026))
                elif self.indexList > 0:
                    # vamos al botón Anterior ya que Siguiente no está activo (estamos al final de la lista)
                    self.setFocus(self.getControl(10025))
            # botón Siguiente
            elif focus == 10026:
                if self.indexList > 0:
                    # vamos al botón Anterior
                    self.setFocus(self.getControl(10025))

        # Accion 2: Flecha derecha
        if action == 2:
            # Obtenemos el foco
            focus = self.getFocusId()

            # botón Anterior
            if focus == 10025:
                if self.indexList + 1 != len(self.listData):
                    # vamos al botón Siguiente
                    self.setFocus(self.getControl(10026))
                else:
                    # vamos al botón Cancelar ya que Siguiente no está activo (estamos al final de la lista)
                    self.setFocus(self.getControl(10027))
            # botón Siguiente
            elif focus == 10026:
                self.setFocus(self.getControl(10027))
            # boton Cancelar
            elif focus == 10027:
                self.setFocus(self.getControl(10028))

        # Pulsa OK, simula click en boton aceptar
        # if action == 107: # es mover el ratón
        #     logger.info("onAction he pulstado ok")
        #     # self.onClick(10028)

        # Pulsa ESC o Atrás, simula click en boton cancelar
        if action in [10, 92]:
            # TODO arreglar
            # self.close()
            self.onClick(10027)
