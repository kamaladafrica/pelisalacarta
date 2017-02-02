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
# tvdb
# ------------------------------------------------------------
# Scraper para el site thetvdb.com usando API v2.1
# Utilizado para obtener datos de series para la biblioteca
# de pelisalacarta y también Kodi.
# ------------------------------------------------------------

import copy
import re
import urllib2

from core import config
from core import jsontools
from core import logger
from core import scrapertools
from core.item import InfoLabels

HOST = "https://api.thetvdb.com"
HOST_IMAGE = "http://thetvdb.com/banners/"
TOKEN = config.get_setting("tvdb_token")

DEFAULT_LANG = "es"
DEFAULT_HEADERS = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, application/vnd.thetvdb.v2.1.1',
        'Accept-Language': DEFAULT_LANG,
        'Authorization': 'Bearer ' + TOKEN,
    }


DICT_STATUS = {'Continuing': 'En emisión', 'Ended': 'Finalizada'}

DICT_GENRE = {
    'Action': 'Acción',
    'Adventure': 'Aventura',
    'Animation': 'Animación',
    'Children': 'Niños',
    'Comedy': 'Comedia',
    'Crime': 'Crimen',
    'Documentary': 'Documental',
    # 'Drama': 'Drama',
    'Family': 'Familiar',
    'Fantasy': 'Fantasía',
    'Food': 'Comida',
    'Game Show': 'Concurso',
    'Home and Garden': 'Hogar y Jardín',
    # 'Horror': 'Horror', 'Mini-Series': 'Mini-Series',
    'Mystery': 'Misterio',
    'News': 'Noticias',
    # 'Reality': 'Telerrealidad',
    'Romance': 'Romántico',
    'Science-Fiction': 'Ciencia-Ficción',
    'Soap': 'Telenovela',
    # 'Special Interest': 'Special Interest',
    'Sport': 'Deporte',
    # 'Suspense': 'Suspense',
    'Talk Show': 'Programa de Entrevistas',
    # 'Thriller': 'Thriller',
    'Travel': 'Viaje',
    # 'Western': 'Western'
}

DICT_MPAA = {'TV-Y': 'Público pre-infantil: niños menores de 6 años', 'TV-Y7': 'Público infantil: desde 7 años',
             'TV-G': 'Público general: sin supervisión familiar', 'TV-PG': 'Guía paterna: Supervisión paternal',
             'TV-14': 'Mayores de 14 años', 'TV-MA': 'Mayores de 17 años'}

otvdb_global = None


def set_infoLabels_item(item):
    """
        Obtiene y fija (item.infoLabels) los datos extras de una serie, capitulo o pelicula.
        @param item: Objeto que representa un pelicula, serie o capitulo. El atributo infoLabels sera modificado
            incluyendo los datos extras localizados.
        @type item: Item


    """
    global otvdb_global

    def __leer_datos(otvdb_aux):
        item.infoLabels = otvdb_aux.get_infoLabels(item.infoLabels)
        if 'infoLabels' in item and 'thumbnail' in item.infoLabels:
            item.thumbnail = item.infoLabels['thumbnail']
        if 'infoLabels' in item and 'fanart' in item.infoLabels['fanart']:
            item.fanart = item.infoLabels['fanart']

    if 'infoLabels' in item and 'season' in item.infoLabels:
        try:
            int_season = int(item.infoLabels['season'])
        except ValueError:
            logger.debug("El numero de temporada no es valido")
            item.contentType = item.infoLabels['mediatype']
            return -1 * len(item.infoLabels)

        if not otvdb_global or \
                (item.infoLabels['tvdb_id'] and otvdb_global.get_id() != item.infoLabels['tvdb_id'])  \
                or (otvdb_global.search_name and otvdb_global.search_name != item.infoLabels['tvshowtitle']):
            if item.infoLabels['tvdb_id']:
                otvdb_global = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])
            else:
                otvdb_global = Tvdb(search=item.infoLabels['tvshowtitle'])

            __leer_datos(otvdb_global)

        if item.infoLabels['episode']:
            try:
                int_episode = int(item.infoLabels['episode'])
            except ValueError:
                logger.debug("El número de episodio (%s) no es valido" % repr(item.infoLabels['episode']))
                item.contentType = item.infoLabels['mediatype']
                return -1 * len(item.infoLabels)

            # Tenemos numero de temporada y numero de episodio validos...
            # ... buscar datos episodio
            item.infoLabels['mediatype'] = 'episode'
            data_episode = otvdb_global.get_info_episode(otvdb_global.get_id(), int_season, int_episode)

            # todo repasar valores que hay que insertar en infoLabels
            if data_episode:
                # todo mirar
                item.infoLabels['title'] = data_episode['episodeName']

                item.infoLabels['plot'] = data_episode.get("overview", "")
                item.thumbnail = HOST_IMAGE + data_episode.get('filename', "")

                item.infoLabels['director'] = ', '.join(sorted(data_episode.get('directors', [])))
                item.infoLabels['writer'] = ', '.join(sorted(data_episode.get("writers", [])))
                item.infoLabels["rating"] = data_episode.get("siteRating", "")

                if data_episode["firstAired"]:
                    item.infoLabels['premiered'] = data_episode["firstAired"].split("-")[2] + "/" + \
                                                   data_episode["firstAired"].split("-")[1] + "/" + \
                                                   data_episode["firstAired"].split("-")[0]

                return len(item.infoLabels)

        else:
            # Tenemos numero de temporada valido pero no numero de episodio...
            # ... buscar datos temporada
            item.infoLabels['mediatype'] = 'season'
            data_season = otvdb_global.get_images(otvdb_global.get_id(), "season", int_season)

            # todo repasar valores que hay que insertar en infoLabels
            if data_season and 'image_season'in data_season:
                item.thumbnail = HOST_IMAGE + data_season['image_season'][0]['fileName']

                return len(item.infoLabels)

    # Buscar...
    else:
        otvdb = copy.copy(otvdb_global)
        # Busquedas por ID...
        if item.infoLabels['tvdb_id']:
            otvdb = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])

        elif item.infoLabels['imdb_id']:
            otvdb = Tvdb(imdb_id=item.infoLabels['imdb_id'])

        # # buscar con otros codigos
        # elif item.infoLabels['zap2it_id']:
        #     # ...Busqueda por tvdb_id
        #     otvdb = Tvdb(zap2it_id=item.infoLabels['zap2it_id'])

        # No se ha podido buscar por ID... se hace por título
        if otvdb is None:
            otvdb = Tvdb(search=item.infoLabels['tvshowtitle'])

        if otvdb and otvdb.get_id():
            # La busqueda ha encontrado un resultado valido
            __leer_datos(otvdb)
            return len(item.infoLabels)


# TODO DOCSTRINGS
class Tvdb:
    # Atributo de clase
    def __init__(self, **kwargs):

        self.__check_token()

        self.result = {}
        self.results = []
        self.search_name = kwargs['search'] = \
            re.sub('\[\\\?(B|I|COLOR)\s?[^\]]*\]', '', kwargs.get('search', ''))

        if kwargs.get('tvdb_id', ''):
            # Busqueda por identificador tvdb
            self.__get_by_id(kwargs.get('tvdb_id', ''))
            if not self.results:
                from platformcode import platformtools
                platformtools.dialog_notification("No se ha encontrado en idioma '%s'" % DEFAULT_LANG,
                                                  "Se busca en idioma 'en'")
                self.__get_by_id(kwargs.get('tvdb_id', ''), "en")

        elif self.search_name:
            # Busqueda por texto
            self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''))
            if not self.results:
                from platformcode import platformtools
                platformtools.dialog_notification("No se ha encontrado en idioma '%s'" % DEFAULT_LANG,
                                                  "Se busca en idioma 'en'")
                self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''), "en")

        if not self.result:
            # No hay resultados de la busqueda
            if kwargs.get('tvdb_id', ''):
                buscando = kwargs.get('tvdb_id', '')
            else:
                buscando = kwargs.get('search', '')
            msg = "La busqueda de %s no dio resultados." % buscando
            logger.debug(msg)

    @classmethod
    def __check_token(cls):
        # logger.info()
        if TOKEN == "":
            cls.__login()
        else:
            # si la fecha no se corresponde con la actual llamamos a refresh_token, ya que el token expira en 24 horas
            from time import gmtime, strftime
            current_date = strftime("%Y-%m-%d", gmtime())

            if config.get_setting("tvdb_token_date", "") != current_date:
                # si se ha renovado el token grabamos la nueva fecha
                if cls.__refresh_token():
                    config.set_setting("tvdb_token_date", current_date)

    @staticmethod
    def __login():
        # logger.info()
        global TOKEN

        apikey = "106B699FDC04301C"

        url = HOST + "/login"
        params = {"apikey": apikey}

        try:
            req = urllib2.Request(url, data=jsontools.dump_json(params), headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error("error en: {0}".format(message))

        else:
            dict_html = jsontools.load_json(html)

            if "token" in dict_html:
                token = dict_html["token"]
                DEFAULT_HEADERS["Authorization"] = "Bearer " + token

                TOKEN = config.set_setting("tvdb_token", token)

    @classmethod
    def __refresh_token(cls):
        # logger.info()
        global TOKEN
        is_success = False

        url = HOST + "/refresh_token"

        try:
            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except urllib2.HTTPError, err:
            logger.info("err.code es %s" % err.code)
            # si hay error 401 es que el token se ha pasado de tiempo y tenemos que volver a llamar a login
            if err.code == 401:
                cls.__login()
            else:
                raise

        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error("error en: {0}".format(message))

        else:
            dict_html = jsontools.load_json(html)
            # logger.error("tokencito {}".format(dict_html))
            if "token" in dict_html:
                token = dict_html["token"]
                DEFAULT_HEADERS["Authorization"] = "Bearer " + token
                TOKEN = config.set_setting("tvdb_token", token)
                is_success = True

        return is_success

    @classmethod
    def get_info_episode(cls, _id, season=1, episode=1, lang=DEFAULT_LANG):
        """
        devuelve los datos de un episodio
        @param _id: identificador de la serie
        @type _id: str
        @param season: numero de temporada [por defecto = 1]
        @type season: int
        @param episode: numero de episodio [por defecto = 1]
        @type episode: int
        @param lang: codigo de idioma para buscar
        @type lang: str
        @rtype: dict
        @return:
        "data": {
                    "id": 0,
                    "airedSeason": 0,
                    "airedEpisodeNumber": 0,
                    "episodeName": "string",
                    "firstAired": "string",
                    "guestStars": [
                        "string"
                    ],
                    "director": "string", # deprecated
                    "directors": [
                        "string"
                    ],
                    "writers": [
                        "string"
                    ],
                    "overview": "string",
                    "productionCode": "string",
                    "showUrl": "string",
                    "lastUpdated": 0,
                    "dvdDiscid": "string",
                    "dvdSeason": 0,
                    "dvdEpisodeNumber": 0,
                    "dvdChapter": 0,
                    "absoluteNumber": 0,
                    "filename": "string",
                    "seriesId": "string",
                    "lastUpdatedBy": "string",
                    "airsAfterSeason": 0,
                    "airsBeforeSeason": 0,
                    "airsBeforeEpisode": 0,
                    "thumbAuthor": 0,
                    "thumbAdded": "string",
                    "thumbWidth": "string",
                    "thumbHeight": "string",
                    "imdbId": "string",
                    "siteRating": 0,
                    "siteRatingCount": 0
                },
        "errors": {
            "invalidFilters": [
                "string"
            ],
            "invalidLanguage": "string",
            "invalidQueryParams": [
                "string"
            ]
        }
        """
        logger.info()
        params = {"airedSeason": "%s" % season, "airedEpisode": "%s" % episode}

        try:
            import urllib
            params = urllib.urlencode(params)

            url = HOST + "/series/{id}/episodes/query?{params}".format(id=_id, params=params)
            DEFAULT_HEADERS["Accept-Language"] = lang
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error("error en: {0}".format(message))

        else:
            dict_html = jsontools.load_json(html)

            if "data" in dict_html and "id" in dict_html["data"][0]:
                return cls.__get_episode_by_id(dict_html["data"][0]["id"])

    @staticmethod
    def __get_episode_by_id(_id, lang=DEFAULT_LANG):
        logger.info()
        dict_html = {}

        url = HOST + "/episodes/{id}".format(id=_id)

        try:
            DEFAULT_HEADERS["Accept-Language"] = lang
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))
            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            if type(ex) == urllib2.HTTPError:
                logger.debug("code es %s " % ex.code)

            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error("error en: {0}".format(message))

        else:
            dict_html = jsontools.load_json(html)
            dict_html = dict_html.pop("data")
        return dict_html

    def __search(self, name, imdb_id, zap2it_id, lang=DEFAULT_LANG):
        """
        Busca una serie a través de una serie de parámetros
        @param name: nombre a buscar
        @type name: str
        @param imdb_id: codigo identificativo de imdb
        @type imdb_id: str
        @param zap2it_id: codigo identificativo de zap2it
        @type zap2it_id: str

        data:{
          "aliases": [
            "string"
          ],
          "banner": "string",
          "firstAired": "string",
          "id": 0,
          "network": "string",
          "overview": "string",
          "seriesName": "string",
          "status": "string"
        }
        """
        logger.info()

        try:

            params = {}
            if name:
                params["name"] = name
            elif imdb_id:
                params["imdbId"] = imdb_id
            elif zap2it_id:
                params["zap2itId"] = zap2it_id

            import urllib
            params = urllib.urlencode(params)

            DEFAULT_HEADERS["Accept-Language"] = lang
            url = HOST + "/search/series?{params}".format(params=params)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            if type(ex) == urllib2.HTTPError:
                logger.debug("code es %s " % ex.code)

            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error("error en: {0}".format(message))

        else:
            dict_html = jsontools.load_json(html)

            if "errors" in dict_html and "invalidLanguage" in dict_html["errors"]:
                # no hay información en idioma por defecto
                return

            else:
                resultado = dict_html["data"]

                # todo revisar
                if len(resultado) > 1:
                    index = 0
                else:
                    index = 0

                logger.debug("resultado {}".format(resultado))
                self.results = resultado
                self.result = resultado[index]

    def __get_by_id(self, _id, lang=DEFAULT_LANG):
        logger.info()
        resultado = {}

        url = HOST + "/series/{id}".format(id=_id)

        try:
            DEFAULT_HEADERS["Accept-Language"] = lang
            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            if type(ex) == urllib2.HTTPError:
                logger.debug("code es %s " % ex.code)

            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error("error en: {0}".format(message))

        else:
            dict_html = jsontools.load_json(html)

            if "errors" in dict_html and "invalidLanguage" in dict_html["errors"]:
                return {}
            else:
                resultado1 = dict_html["data"]

                logger.debug("resultado1 {}".format(dict_html))

                resultado2 = self.get_images(_id, image="poster")
                resultado3 = self.get_images(_id, image="fanart")
                resultado4 = self.__get_tvshow_cast(_id, lang)

                resultado = resultado1.copy()
                resultado.update(resultado2)
                resultado.update(resultado3)
                resultado.update(resultado4)

                logger.debug("resultado {}".format(resultado))
                self.results = resultado
                self.result = resultado

        return resultado

    @staticmethod
    def get_images(_id, image="poster", season=1, lang="en"):
        """
        obtiene un tipo imagenes para una serie para un idioma.
        @param _id: identificador de la serie
        @type _id: str
        @param image: codigo de busqueda, ["poster" (por defecto), "fanart", "season"]
        @type image: str
        @type season: numero de temporada
        @param lang: código de idioma para el que se busca
        @type lang: str
        @return: diccionario con el tipo de imagenes elegidas.
        @rtype: dict

        """
        logger.info()

        params = {}
        if image == "poster":
            params["keyType"] = "poster"
        elif image == "fanart":
            params["keyType"] = "fanart"
            params["subKey"] = "graphical"
        elif image == "season":
            params["keyType"] = "season"
            params["subKey"] = "%s" % season

        try:

            import urllib
            params = urllib.urlencode(params)
            DEFAULT_HEADERS["Accept-Language"] = lang
            url = HOST + "/series/{id}/images/query?{params}".format(id=_id, params=params)
            logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

            req = urllib2.Request(url, headers=DEFAULT_HEADERS)
            response = urllib2.urlopen(req)
            html = response.read()
            response.close()

        except Exception, ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.error("error en: {0}".format(message))

            return {}

        else:
            dict_html = jsontools.load_json(html)

            dict_html["image_" + image] = dict_html.pop("data")

            return dict_html

    @staticmethod
    def __get_tvshow_cast(_id, lang=DEFAULT_LANG):
        """
        obtiene el casting de una serie
        @param _id: codigo de la serie
        @type _id: str
        @param lang: codigo idioma para buscar
        @type lang: str
        @return: diccionario con los actores
        @rtype: dict
        """
        logger.info()

        url = HOST + "/series/{id}/actors".format(id=_id)
        DEFAULT_HEADERS["Accept-Language"] = lang
        logger.debug("url: %s, \nheaders: %s" % (url, DEFAULT_HEADERS))

        req = urllib2.Request(url, headers=DEFAULT_HEADERS)
        response = urllib2.urlopen(req)
        html = response.read()
        response.close()

        dict_html = jsontools.load_json(html)

        dict_html["cast"] = dict_html.pop("data")
        return dict_html

    def get_id(self):
        """
        @return: Devuelve el identificador Tvdb de la serie cargada o una cadena vacia en caso de que no
            hubiese nada cargado. Se puede utilizar este metodo para saber si una busqueda ha dado resultado o no.
        @rtype: str
        """
        return str(self.result.get('id', ""))

    def get_list_resultados(self):
        list_result = []

        for i in self.results:
            dict_html = self.__get_by_id(i['id'])
            if not dict_html:
                dict_html = self.__get_by_id(i['id'], "en")
            # todo mirar de ordenar por el año
            list_result.append(dict_html)

        return list_result

    def get_infoLabels(self, infoLabels=None, origen=None):
        """
        @param infoLabels: Informacion extra de la pelicula, serie, temporada o capitulo.
        @type infoLabels: dict
        @param origen: Diccionario origen de donde se obtiene los infoLabels, por omision self.result
        @type origen: dict
        @return: Devuelve la informacion extra obtenida del objeto actual. Si se paso el parametro infoLables, el valor
        devuelto sera el leido como parametro debidamente actualizado.
        @rtype: dict
        """

        if infoLabels:
            ret_infoLabels = InfoLabels(infoLabels)
        else:
            ret_infoLabels = InfoLabels()

        # Iniciar listados
        l_castandrole = ret_infoLabels.get('castandrole', [])

        # logger.debug("self.result {}".format(self.result))

        if not origen:
            origen = self.result

        # todo revisar
        # if 'credits' in origen.keys():
        #     dic_origen_credits = origen['credits']
        #     origen['credits_cast'] = dic_origen_credits.get('cast', [])
        #     origen['credits_crew'] = dic_origen_credits.get('crew', [])
        #     del origen['credits']

        items = origen.items()

        # todo revisar
        # # Informacion Temporada/episodio
        # if ret_infoLabels['season'] and self.temporada.get(ret_infoLabels['season']):
        #     # Si hay datos cargados de la temporada indicada
        #     episodio = -1
        #     if ret_infoLabels['episode']:
        #         episodio = ret_infoLabels['episode']
        #
        #     items.extend(self.get_episodio(ret_infoLabels['season'], episodio).items())

        for k, v in items:
            if not v:
                continue

            if k == 'overview':
                ret_infoLabels['plot'] = v

            elif k == 'runtime':
                ret_infoLabels['duration'] = int(v) * 60

            elif k == 'firstAired':
                ret_infoLabels['year'] = int(v[:4])
                ret_infoLabels['premiered'] = v.split("-")[2] + "/" + v.split("-")[1] + "/" + v.split("-")[0]

            # todo revisar
            # elif k == 'original_title' or k == 'original_name':
            #     ret_infoLabels['originaltitle'] = v

            elif k == 'siteRating':
                ret_infoLabels['rating'] = float(v)

            elif k == 'status':
                # se traduce los estados de una serie
                ret_infoLabels['status'] = DICT_STATUS.get(v, v)

            elif k == 'image_poster':
                # obtenemos la primera imagen de la lista
                ret_infoLabels['thumbnail'] = HOST_IMAGE + v[0]['fileName']

            elif k == 'image_fanart':
                # obtenemos la primera imagen de la lista
                ret_infoLabels['fanart'] = HOST_IMAGE + v[0]['fileName']

            # # no disponemos de la imagen de fondo
            # elif k == 'banner':
            #     ret_infoLabels['fanart'] = HOST_IMAGE + v

            elif k == 'id':
                ret_infoLabels['tvdb_id'] = v

            elif k == 'imdbId':
                ret_infoLabels['imdb_id'] = v
                # no se muestra
                # ret_infoLabels['code'] = v

            elif k in "rating":
                # traducimos la clasificación por edades (content rating system)
                ret_infoLabels['mpaa'] = DICT_MPAA.get(v, v)

            elif k in "genre":
                genre_list = ""
                for index, i in enumerate(v):
                    if index > 0:
                        genre_list += ", "

                    # traducimos los generos
                    genre_list += DICT_GENRE.get(i, i)

                ret_infoLabels['genre'] = genre_list

            elif k == 'seriesName':  # or k == 'name' or k == 'title':
                ret_infoLabels['title'] = v

            elif k == 'cast':  # or k == 'temporada_cast' or k == 'episodio_guest_stars':
                dic_aux = dict((name, character) for (name, character) in l_castandrole)
                l_castandrole.extend([(p['name'], p['role']) for p in v if p['name'] not in dic_aux.keys()])

            else:
                logger.debug("Atributos no añadidos: %s=%s" % (k, v))
                pass

        # Ordenar las listas y convertirlas en str si es necesario
        if l_castandrole:
            ret_infoLabels['castandrole'] = sorted(l_castandrole, key=lambda tup: tup[0])

        logger.debug("ret_infoLabels %s" % ret_infoLabels)

        return ret_infoLabels


def find_and_set_infoLabels(item):
    logger.info()

    global otvdb_global
    tvdb_result = None

    title = item.contentSerieName
    # Si el titulo incluye el (año) se lo quitamos
    year = scrapertools.find_single_match(title, "^.+?\s*(\(\d{4}\))$")
    if year:
        title = title.replace(year, "").strip()
        item.infoLabels['year'] = year[1:-1]

    if not item.infoLabels.get("tvdb_id"):
        if not item.infoLabels.get("imdb_id"):
            otvdb_global = Tvdb(search=title, year=item.infoLabels['year'])
        else:
            otvdb_global = Tvdb(imdb_id=item.infoLabels.get("imdb_id"))

    elif not otvdb_global or otvdb_global.result.get("id") != item.infoLabels['tvdb_id']:
        otvdb_global = Tvdb(tvdb_id=item.infoLabels['tvdb_id'])  # , tipo=tipo_busqueda, idioma_busqueda="es")

    results = otvdb_global.get_list_resultados()

    logger.debug("results es %s" % results)

    if len(results) > 1:
        from platformcode import platformtools
        tvdb_result = platformtools.show_video_info(results, item=item, scraper=Tvdb,
                                                    caption="[%s]: Selecciona la serie correcta" % title)
    elif len(results) > 0:
        tvdb_result = results[0]

    # todo revisar
    if isinstance(item.infoLabels, InfoLabels):
        infoLabels = item.infoLabels
    else:
        infoLabels = InfoLabels()

    if tvdb_result:
        infoLabels['tvdb_id'] = tvdb_result['id']
        infoLabels['url_scraper'] = "http://thetvdb.com/?tab=series&id=%s" % (infoLabels['tvdb_id'])
        item.infoLabels = infoLabels
        set_infoLabels_item(item)

        return True

    else:
        item.infoLabels = infoLabels
        return False
