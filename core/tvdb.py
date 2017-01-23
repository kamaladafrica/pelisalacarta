#-*- coding: utf-8 -*-
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

import re

from core import scrapertools
from core import httptools
from core import logger
from core.item import InfoLabels

def tvdb_series_by_title(title, idioma="es"):
    # Esta funcion proporciona la informacion minima requerida
    # se puede ampliar con mas informacion o adaptandola a la nueva API
    list_series = []
    limite = 8

    SeriesByTitleUrl = 'http://thetvdb.com/api/GetSeries.php?seriesname=%s&language=%s' % \
                       (title.replace(' ', '%20'), idioma)
    logger.info(SeriesByTitleUrl)
    data = httptools.downloadpage(SeriesByTitleUrl).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<Series>(.*?)</Series>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for serie in matches:
        info = {"type": "tv", "mediatype": "tvshow"}
        info["tvdb_id"] = scrapertools.find_single_match(serie, '<id>([^<]*)</id>')
        if info["tvdb_id"]:
            info["imdb_id"] = scrapertools.find_single_match(serie, '<IMDB_ID>([^<]*)</IMDB_ID>')
            info["title"] = scrapertools.find_single_match(serie, '<SeriesName>([^<]*)</SeriesName>')
            #info["date"] = scrapertools.find_single_match(serie, '<FirstAired>([^<]*)</FirstAired>')
            info["tvdb_id"] = scrapertools.find_single_match(serie, '<id>([^<]*)</id>')
            info["plot"] = scrapertools.find_single_match(serie, '<Overview>([^<]*)</Overview>')
            info["url_scraper"] = "http://thetvdb.com/?tab=series&id=" + info["tvdb_id"]

            # Recuperar imagenes
            BannersBySeriesIdUrl = 'http://thetvdb.com/api/1D62F2F90030C444/series/%s/banners.xml' % info["tvdb_id"]
            data = scrapertools.cache_page(BannersBySeriesIdUrl)
            data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

            patron = '<Banner>(.*?)</Banner>'
            banners = scrapertools.find_multiple_matches(data, patron)
            for banner in banners:
                BannerType =  scrapertools.find_single_match(banner, '<BannerType>([^<]*)</BannerType>')
                if BannerType == 'fanart' and not "fanart" in info:
                    info["fanart"] = 'http://thetvdb.com/banners/' + \
                                     scrapertools.find_single_match(banner, '<BannerPath>([^<]*)</BannerPath>')
                if BannerType == 'poster' and not "thumbnail" in info:
                    info["thumbnail"] = 'http://thetvdb.com/banners/' + \
                                     scrapertools.find_single_match(banner, '<BannerPath>([^<]*)</BannerPath>')
                if "fanart" in info and "thumbnail" in info:
                    break


            list_series.append(info)
            limite -= 1
            if limite == 0:
                break

    logger.debug(list_series)
    return list_series

def find_and_set_infoLabels(item):
    logger.info()
    tvdb_result = None

    title = item.contentSerieName
    # Si el titulo incluye el (año) se lo quitamos
    year = scrapertools.find_single_match(title, "^.+?\s*(\(\d{4}\))$")
    if year:
        title = title.replace(year, "").strip()
        #item.infoLabels['year'] = year[1:-1]

    results = tvdb_series_by_title(title)

    if len(results) > 1:
        from platformcode import platformtools
        tvdb_result = platformtools.show_video_info(results, item=item,
                                                   caption="[%s]: Selecciona la serie correcta" % title)
    elif len(results) > 0:
        tvdb_result = results[0]

    if isinstance(item.infoLabels, InfoLabels):
        infoLabels = item.infoLabels
    else:
        infoLabels = InfoLabels()

    if tvdb_result:
        infoLabels.update(tvdb_result)
        item.infoLabels = infoLabels
        #logger.debug(item)
        return True

    #item.infoLabels = infoLabels
    return False

