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

# Traducciones - Inicio
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
# Traducciones - Fin

otvdb_global = None


def find_and_set_infoLabels(item):
    logger.info()
    from platformcode import platformtools
    p_dialog = platformtools.dialog_progress_bg("Buscando información de la serie", "Espere por favor...")

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

    p_dialog.update(50, "Buscando información de la serie", "Obteniendo resultados...")
    results = otvdb_global.get_list_results()
    logger.debug("results es %s" % results)

    p_dialog.update(100, "Buscando información de la serie", "Encontrados %s posibles coincidencias" % len(results))

    p_dialog.close()

    if len(results) > 1:
        tvdb_result = platformtools.show_video_info(results, item=item, scraper=Tvdb,
                                                    caption="[%s]: Selecciona la serie correcta" % title)
    elif len(results) > 0:
        tvdb_result = results[0]

    # todo revisar
    if isinstance(item.infoLabels, InfoLabels):
        logger.debug("es instancia de infoLabels")
        infoLabels = item.infoLabels
    else:
        logger.debug("NO ES instancia de infoLabels")
        infoLabels = InfoLabels()

    if tvdb_result:
        infoLabels['tvdb_id'] = tvdb_result['id']
        item.infoLabels = infoLabels
        set_infoLabels_item(item)

        return True

    else:
        item.infoLabels = infoLabels
        return False


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

            lang = DEFAULT_LANG
            if otvdb_global.lang:
                lang = otvdb_global.lang

            # page = 1
            # _id = None
            # while not _id:
            #     if not list_episode:
            #         list_episode = otvdb_global.get_list_episodes(otvdb_global.get_id(), page)
            #
            #     for e in list_episode['data']:
            #         if e['airedSeason'] == int_season and e['airedEpisodeNumber'] == int_episode:
            #             _id = e['id']
            #             break
            #
            #     _next = list_episode['links']['next']
            #     if type(_next) == int:
            #         page = _next
            #     else:
            #         break
            #
            # data_episode = otvdb_global.__get_episode_by_id(_id, lang)





            data_episode = otvdb_global.get_info_episode(otvdb_global.get_id(), int_season, int_episode, lang)

            # todo repasar valores que hay que insertar en infoLabels
            if data_episode:
                item.infoLabels['title'] = data_episode['episodeName']
                # fix en casos que el campo desde la api era null--> None
                if data_episode["overview"] is not None:
                    item.infoLabels['plot'] = data_episode["overview"]

                item.thumbnail = HOST_IMAGE + data_episode.get('filename', "")

                item.infoLabels["rating"] = data_episode.get("siteRating", "")
                item.infoLabels['director'] = ', '.join(sorted(data_episode.get('directors', [])))
                item.infoLabels['writer'] = ', '.join(sorted(data_episode.get("writers", [])))

                if data_episode["firstAired"]:
                    item.infoLabels['premiered'] = data_episode["firstAired"].split("-")[2] + "/" + \
                                                   data_episode["firstAired"].split("-")[1] + "/" + \
                                                   data_episode["firstAired"].split("-")[0]
                    item.infoLabels['aired'] = item.infoLabels['premiered']

                guest_stars = data_episode.get("guestStars", [])
                l_castandrole = item.infoLabels.get("castandrole", [])
                l_castandrole.extend([(p, '') for p in guest_stars])
                item.infoLabels['castandrole'] = l_castandrole

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


def get_nfo(item):
    """
    Devuelve la información necesaria para que se scrapee el resultado en la biblioteca de kodi,

    @param item: elemento que contiene los datos necesarios para generar la info
    @type item: Item
    @rtype: str
    @return:
    """
    info_nfo = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'

    if "season" in item.infoLabels and "episode" in item.infoLabels:
        info_nfo += '<episodedetails><title>%s</title>' % item.infoLabels['title']
        info_nfo += '<showtitle>%s</showtitle>' % item.infoLabels['tvshowtitle']
        info_nfo += '<ratings><rating name="default" max="10" default="true"><value>%s</value><votes>%s</votes>' \
                    '</rating></ratings>' % (item.infoLabels['rating'], item.infoLabels['votes'])

        info_nfo += '<thumb>%s</thumb>' % item.thumbnail

        info_nfo += array_to_node(item.infoLabels['director'], 'director')
        info_nfo += array_to_node(item.infoLabels['writer'], 'credits')

        if item.infoLabels['aired']:
            info_nfo += '<aired>%s</aired>' % (item.infoLabels['aired'].split("/")[2] + "-" +
                                               item.infoLabels['aired'].split("/")[1] + "-" +
                                               item.infoLabels['aired'].split("/")[0])

        info_nfo = set_nfo_casting(info_nfo, item.infoLabels['castandrole'])

        info_nfo += '<plot>%s<plot>' % item.plot
        info_nfo += '</episodedetails>\n'

        # info_nfo += "http://thetvdb.com/?tab=episode&seriesid=%s&seasonid=%s&id=%s\n" % \
        #            (item.infoLabels['tvdb_id'], item.season_id, item.episode_id)

        # ----    <title>Capítulo 1</title>
        # ----    <showtitle>Legión</showtitle>
        # ---    <ratings>
        #  ---       <rating name="default" max="10" default="true">
        #  ---           <value>9.000000</value>
        #  ---           <votes>5</votes>
        #  --       </rating>
        # ---    </ratings>
        #     <userrating>0</userrating>
        #     <top250>0</top250>
        #     <season>1</season>
        #     <episode>1</episode>
        #     <displayseason>-1</displayseason>
        #     <displayepisode>-1</displayepisode>
        #     <outline></outline>
        # ----    <plot>David comienza a considerar que las voces que escucha en su cabeza pueden ser reales.</plot>
        #     <tagline></tagline>
        #     <runtime>45</runtime>
        # ----    <thumb>http://thetvdb.com/banners/episodes/320724/5869915.jpg</thumb>
        # heredado    <mpaa></mpaa>
        #     <playcount>0</playcount>
        #     <lastplayed></lastplayed>
        #     <file></file>
        # ----    <path>special://home/userdata/addon_data/plugin.video.pelisalacarta/library/SERIES/legión [tt5114356]/</path>
        #     <filenameandpath>special://home/userdata/addon_data/plugin.video.pelisalacarta/library/SERIES/legión [tt5114356]/1x01.strm</filenameandpath>
        #     <basepath>special://home/userdata/addon_data/plugin.video.pelisalacarta/library/SERIES/legión [tt5114356]/1x01.strm</basepath>
        #     <id>5869915</id>
        #     <uniqueid type="unknown" default="true">5869915</uniqueid>
        # heredado    <genre>Action</genre>
        # heredado    <genre>Drama</genre>
        #     <credits>Noah Hawley</credits>
        #     <director>Noah Hawley</director>
        #     <premiered>2017-02-08</premiered>
        #     <year>2017</year>
        # heredado    <status></status>
        #     <code></code>
        # ---    <aired>2017-02-08</aired>
        # heredado    <studio>FX (US)</studio>
        #     <trailer></trailer>
        #  ---   <actor>
        #   ---      <name>Dan Stevens</name>
        #   ---      <role>David Haller</role>
        #         <order>0</order>
        #         <thumb>http://thetvdb.com/banners/actors/411764.jpg</thumb>
        #  ---   </actor>
        #  ---   <actor>
        #  ---       <name>Rachel Keller</name>
        #  ---       <role>Syd Barrett</role>
        #         <order>1</order>
        #         <thumb>http://thetvdb.com/banners/actors/411763.jpg</thumb>
        #  ---   </actor>
        #     <resume>
        #         <position>0.000000</position>
        #         <total>0.000000</total>
        #     </resume>
        #     <dateadded>2017-02-11 00:06:37</dateadded>
        #     <art>
        #         <thumb>http://thetvdb.com/banners/episodes/320724/5869915.jpg</thumb>
        #     </art>

    else:
        info_nfo += '<tvshow><title>%s</title>' % item.infoLabels['title']

        info_nfo += '<ratings><rating name="default" max="10" default="true"><value>%s</value><votes>%s</votes>' \
                    '</rating></ratings>' % (item.infoLabels['rating'], item.infoLabels['votes'])

        info_nfo += '<thumb aspect="poster">%s</thumb>' % item.thumbnail
        info_nfo += '<fanart><thumb>%s</thumb></fanart>' % item.fanart
        info_nfo += '<year>%s</year>' % item.infoLabels['year']
        info_nfo += '<mpaa>%s</mpaa>' % item.infoLabels['mpaa']

        info_nfo += array_to_node(item.infoLabels['genre'], 'genre')
        info_nfo += '<premiered>%s</premiered>' % (item.infoLabels['premiered'].split("/")[2] + "-" +
                                                   item.infoLabels['premiered'].split("/")[1] + "-" +
                                                   item.infoLabels['premiered'].split("/")[0])

        info_nfo += '<status>%s</status>' % item.infoLabels['status']
        info_nfo += '<studio>%s</studio>' % item.infoLabels['studio']

        # logger.info("el casting es %s " % item.infoLabels['tvdb_cast'])
        # for e in item.infoLabels['tvdb_cast']:
        #     info_nfo += '<actor><name>%s</name><role>%s</role><order>%s</order><thumb>%s</thumb></actor>' \
        #               % (e.get("name", ""), e.get("role", ""), e.get("sortOrder", 0), HOST_IMAGE + e.get("image", ""))
        info_nfo = set_nfo_casting(info_nfo, item.infoLabels['castandrole'])

        info_nfo += '<plot>%s<plot>' % item.plot
        info_nfo += '</tvshow>\n'

        # <title>Legión</title> ---
        # <showtitle>Legión</showtitle>
        # <ratings> --------
        #     <rating name="default" max="10" default="true">---
        #         <value>8.200000</value>---
        #         <votes>6</votes>----
        #     </rating>----
        # </ratings>---
        # <userrating>0</userrating>
        # <top250>0</top250>
        # <season>1</season>
        # <episode>1</episode>
        # <displayseason>-1</displayseason>
        # <displayepisode>-1</displayepisode>
        # <outline></outline>
        # ---- <plot>Se centra en David Haller, un hombre que desde que era adolescente ha tenido que luchar contra una enfermedad mental. Diagnóstico: esquizofrenia. Durante años ha ido entrando y saliendo de diferentes hospitales psiquiátricos para tratarse, pero después de un extraño encuentro con un paciente, se tiene que enfrentar a la posibilidad de que las voces que escucha en su cabeza y las visiones que ve, podrían ser reales. Legion es hijo de Gabrielle Haller y Charles Xavier, el fundador de los X-Men y es uno de los mutantes más poderosos, pero sus diferentes poderes están divididos entre sus múltiples personalidades.</plot>
        # <tagline></tagline>
        # <runtime>45</runtime>
        # <thumb aspect="banner">http://thetvdb.com/banners/graphical/320724-g3.jpg</thumb>
        # <thumb aspect="banner">http://thetvdb.com/banners/graphical/320724-g.jpg</thumb>
        # <thumb aspect="banner">http://thetvdb.com/banners/graphical/320724-g2.jpg</thumb>
        # <thumb aspect="banner">http://thetvdb.com/banners/graphical/320724-g4.jpg</thumb>
        # <thumb aspect="banner">http://thetvdb.com/banners/text/320724.jpg</thumb>
        # <thumb aspect="poster" type="season" season="1">http://thetvdb.com/banners/seasons/320724-1.jpg</thumb>
        # <thumb aspect="poster">http://thetvdb.com/banners/posters/320724-1.jpg</thumb>
        # <thumb aspect="poster">http://thetvdb.com/banners/posters/320724-4.jpg</thumb>
        # <thumb aspect="poster">http://thetvdb.com/banners/posters/320724-2.jpg</thumb>
        # <thumb aspect="poster">http://thetvdb.com/banners/posters/320724-3.jpg</thumb>
        # <thumb aspect="poster" type="season" season="-1">http://thetvdb.com/banners/posters/320724-1.jpg</thumb>
        # <thumb aspect="poster" type="season" season="-1">http://thetvdb.com/banners/posters/320724-4.jpg</thumb>
        # <thumb aspect="poster" type="season" season="-1">http://thetvdb.com/banners/posters/320724-2.jpg</thumb>
        # <thumb aspect="poster" type="season" season="-1">http://thetvdb.com/banners/posters/320724-3.jpg</thumb>
        # <fanart url="http://thetvdb.com/banners/">
        #     <thumb dim="1920x1080" colors="" preview="_cache/fanart/original/320724-3.jpg">fanart/original/320724-3.jpg</thumb>
        #     <thumb dim="1920x1080" colors="" preview="_cache/fanart/original/320724-6.jpg">fanart/original/320724-6.jpg</thumb>
        #     <thumb dim="1280x720" colors="" preview="_cache/fanart/original/320724-2.jpg">fanart/original/320724-2.jpg</thumb>
        #     <thumb dim="1920x1080" colors="" preview="_cache/fanart/original/320724-7.jpg">fanart/original/320724-7.jpg</thumb>
        #     <thumb dim="1280x720" colors="" preview="_cache/fanart/original/320724-9.jpg">fanart/original/320724-9.jpg</thumb>
        #     <thumb dim="1920x1080" colors="" preview="_cache/fanart/original/320724-1.jpg">fanart/original/320724-1.jpg</thumb>
        #     <thumb dim="1920x1080" colors="" preview="_cache/fanart/original/320724-5.jpg">fanart/original/320724-5.jpg</thumb>
        #     <thumb dim="1920x1080" colors="" preview="_cache/fanart/original/320724-8.jpg">fanart/original/320724-8.jpg</thumb>
        #     <thumb dim="1920x1080" colors="" preview="_cache/fanart/original/320724-4.jpg">fanart/original/320724-4.jpg</thumb>
        # </fanart>
        # ----<mpaa></mpaa>
        # <playcount>0</playcount>
        # <lastplayed></lastplayed>
        # <file></file>
        # ----<path>special://home/userdata/addon_data/plugin.video.pelisalacarta/library/SERIES/legión [tt5114356]/</path>
        # <filenameandpath></filenameandpath>
        # <basepath>special://home/userdata/addon_data/plugin.video.pelisalacarta/library/SERIES/legión [tt5114356]/</basepath>
        # <episodeguide>
        #     <url cache="320724-es.xml">http://thetvdb.com/api/1D62F2F90030C444/series/320724/all/es.zip</url>
        # </episodeguide>
        # <id>320724</id>
        # <uniqueid type="unknown" default="true">320724</uniqueid>
        # ----<genre>Action</genre>
        # ----<genre>Drama</genre>
        # ----<genre>Fantasy</genre>
        # -----<premiered>2017-02-08</premiered>
        # ----<year>2017</year>
        # ----<status></status>
        # <code></code>
        # <aired></aired>
        # ----<studio>FX (US)</studio>
        # <trailer></trailer>
        # ---<actor>
        # ---    <name>Dan Stevens</name>
        #     <role>David Haller</role>
        #     <order>0</order>
        #     <thumb>http://thetvdb.com/banners/actors/411764.jpg</thumb>
        # ---</actor>
        # ---<actor>
        # ---    <name>Rachel Keller</name>
        # ---    <role>Syd Barrett</role>
        #     <order>1</order>
        #     <thumb>http://thetvdb.com/banners/actors/411763.jpg</thumb>
        # ---</actor>
        # <resume>
        #     <position>0.000000</position>
        #     <total>0.000000</total>
        # </resume>
        # <dateadded>2017-02-11 00:06:37</dateadded>
        # <art>
        #     <banner>http://thetvdb.com/banners/graphical/320724-g3.jpg</banner>
        #     <fanart>http://thetvdb.com/banners/fanart/original/320724-3.jpg</fanart>
        #     <poster>http://thetvdb.com/banners/posters/320724-1.jpg</poster>
        #     <season num="-1">
        #         <poster>http://thetvdb.com/banners/posters/320724-1.jpg</poster>
        #     </season>
        #     <season num="0" />
        #     <season num="1">
        #         <poster>http://thetvdb.com/banners/seasons/320724-1.jpg</poster>
        #     </season>
        # </art>

    return info_nfo


def array_to_node(array, node_name):
    list_genre = array.split(", ")
    result = ""
    for i in list_genre:
        result += '<%s>%s</%s>' % (node_name, i, node_name)
    return result


def set_nfo_casting(info_nfo, casting):
    for index, e in enumerate(casting):
        info_nfo += '<actor><name>%s</name><role>%s</role><order>%s</order><thumb></thumb></actor>' % \
                    (e[0], e[1], index)
    return info_nfo


# TODO DOCSTRINGS
class Tvdb:
    # Atributo de clase
    def __init__(self, **kwargs):

        self.__check_token()

        self.result = {}
        self.list_results = []
        self.lang = ""
        self.search_name = kwargs['search'] = \
            re.sub('\[\\\?(B|I|COLOR)\s?[^\]]*\]', '', kwargs.get('search', ''))

        if kwargs.get('tvdb_id', ''):
            # Busqueda por identificador tvdb
            self.__get_by_id(kwargs.get('tvdb_id', ''))
            if not self.list_results and config.get_setting("tvdb_retry_eng", "biblioteca"):
                from platformcode import platformtools
                platformtools.dialog_notification("No se ha encontrado en idioma '%s'" % DEFAULT_LANG,
                                                  "Se busca en idioma 'en'")
                self.__get_by_id(kwargs.get('tvdb_id', ''), "en")
                self.lang = "en"

        elif self.search_name:
            # Busqueda por texto
            self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''))
            if not self.list_results and config.get_setting("tvdb_retry_eng", "biblioteca"):
                from platformcode import platformtools
                platformtools.dialog_notification("No se ha encontrado en idioma '%s'" % DEFAULT_LANG,
                                                  "Se busca en idioma 'en'")
                self.__search(kwargs.get('search', ''), kwargs.get('imdb_id', ''), kwargs.get('zap2it_id', ''), "en")
                self.lang = "en"

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
                return cls.__get_episode_by_id(dict_html["data"][0]["id"], lang)

    @classmethod
    def get_list_episodes(cls, _id, page=1):
        """
        devuelve los datos de un episodio
        @param _id: identificador de la serie
        @type _id: str
        @param page: numero de pagina a buscar [por defecto = 1]
        @type page: int
        @rtype: dict
        @return:
        {
            "links": {
                "first": 0,
                "last": 0,
                "next": 0,
                "previous": 0
              },
            "data": [
                {
                    "absoluteNumber": 0,
                    "airedEpisodeNumber": 0,
                    "airedSeason": 0,
                    "dvdEpisodeNumber": 0,
                    "dvdSeason": 0,
                    "episodeName": "string",
                    "id": 0,
                    "overview": "string",
                    "firstAired": "string",
                    "lastUpdated": 0
                }
            ],
            "errors": {
                "invalidFilters": [
                  "string"
                ],
                "invalidLanguage": "string",
                "invalidQueryParams": [
                  "string"
                ]
            }
        }
        """
        logger.info()
        # params = {"airedSeason": "%s" % season, "airedEpisode": "%s" % episode}

        try:
            # import urllib
            # params = urllib.urlencode(params)

            url = HOST + "/series/{id}/episodes?page={params}".format(id=_id, page=page)
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

            logger.info("dict_html %s" % dict_html)

            return dict_html

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

            logger.info("dict_html %s" % dict_html)
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
                self.list_results = resultado
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
                self.list_results = [resultado]
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

    def get_list_results(self):
        logger.info()
        list_results = []

        # logger.info("long es: %s" % len(self.list_results))
        # logger.info("results es: %s" % self.list_results)

        # TODO revisar condicion
        # si tenemos un resultado y tiene seriesName, ya tenemos la info de la serie, no hace falta volver a buscar
        if len(self.list_results) == 1 and "seriesName" in self.result:
            list_results.append(self.result)
        else:
            for e in self.list_results:
                logger.info("e es: %s" % e)
                logger.info("id es: %s" % e['id'])
                dict_html = self.__get_by_id(e['id'])
                # todo revisar si hace falta
                if not dict_html:
                    dict_html = self.__get_by_id(e['id'], "en")
                # todo mirar de ordenar por el año
                list_results.append(dict_html)

        return list_results

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
            logger.debug("es instancia de infoLabels")
            ret_infoLabels = InfoLabels(infoLabels)
        else:
            logger.debug("NO ES instancia de infoLabels")
            ret_infoLabels = InfoLabels()
            # fix
            ret_infoLabels['mediatype'] = 'tvshow'

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

            elif k == 'siteRatingCount':
                ret_infoLabels['votes'] = v

            elif k == 'status':
                # se traduce los estados de una serie
                ret_infoLabels['status'] = DICT_STATUS.get(v, v)

            # no soy partidario de poner la cadena como studio pero es como lo hace el scraper de manera genérica
            elif k == 'network':
                ret_infoLabels['studio'] = v

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
                # if len(origen.get('aliases', [])) > 0:
                #     ret_infoLabels['title'] = v + " " + origen.get('aliases', [''])[0]
                # else:
                #     ret_infoLabels['title'] = v
                # logger.info("el titulo es %s " % ret_infoLabels['title'])
                ret_infoLabels['title'] = v

            elif k == 'cast':
                dic_aux = dict((name, character) for (name, character) in l_castandrole)
                l_castandrole.extend([(p['name'], p['role']) for p in v if p['name'] not in dic_aux.keys()])

            else:
                logger.debug("Atributos no añadidos: %s=%s" % (k, v))
                pass

        # Ordenar las listas y convertirlas en str si es necesario
        if l_castandrole:
            ret_infoLabels['castandrole'] = l_castandrole

        logger.debug("ret_infoLabels %s" % ret_infoLabels)

        return ret_infoLabels
