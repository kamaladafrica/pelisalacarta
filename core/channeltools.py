# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# tvalacarta - XBMC Plugin
# ------------------------------------------------------------
# channeltools
# Herramientas para trabajar con canales
# ------------------------------------------------------------

import os
import re

import config
import logger
import scrapertools


def is_adult(channel_name):
    logger.info("pelisalacarta.core.channeltools is_adult channel_name="+channel_name)

    channel_parameters = get_channel_parameters(channel_name)

    return channel_parameters["adult"] == "true"


def get_channel_parameters(channel_name):
    logger.info("pelisalacarta.core.channeltools get_channel_parameters channel_name="+channel_name)

    channel_xml = os.path.join(config.get_runtime_path(), 'channels', channel_name+".xml")

    if os.path.exists(channel_xml):
        logger.info("pelisalacarta.core.channeltools get_channel_parameters "+channel_name+".xml found")

        infile = open(channel_xml, "rb")
        data = infile.read()
        infile.close()

        # TODO: Pendiente del json :)
        channel_parameters = {}
        channel_parameters["title"] = scrapertools.find_single_match(data, "<name>([^<]*)</name>")
        channel_parameters["channel"] = scrapertools.find_single_match(data, "<id>([^<]*)</id>")
        channel_parameters["active"] = scrapertools.find_single_match(data, "<active>([^<]*)</active>")
        channel_parameters["adult"] = scrapertools.find_single_match(data, "<adult>([^<]*)</adult>")
        channel_parameters["language"] = scrapertools.find_single_match(data, "<language>([^<]*)</language>")
        channel_parameters["thumbnail"] = scrapertools.find_single_match(data, "<thumbnail>([^<]*)</thumbnail>")
        channel_parameters["bannermenu"] = scrapertools.find_single_match(data, "<bannermenu>([^<]*)</bannermenu>")
        channel_parameters["fanart"] = scrapertools.find_single_match(data, "<fanart>([^<]*)</fanart>")
        channel_parameters["include_in_global_search"] = scrapertools.find_single_match(
            data, "<include_in_global_search>([^<]*)</include_in_global_search>")
        channel_parameters["type"] = "generic"

        category_list = []
        matches = scrapertools.find_multiple_matches(data, "<category>([^<]*)</category>")
        for match in matches:
            category_list.append(match)

        channel_parameters["categories"] = category_list

        dict_tvshow_lang = dict()
        data = re.sub(r"\n|\r|\t|\s{2}", "", data)
        info = scrapertools.find_single_match(data, "<tvshow_lang>(.*?)</tvshow_lang>")

        if info:
            patron = "<(.*?)>(.*?)</[^>]+>"
            matches = re.compile(patron, re.DOTALL).findall(info)
            for key, value in matches:
                dict_tvshow_lang.update({key: value})

        channel_parameters["dict_tvshow_lang"] = dict_tvshow_lang

        list_quality = list()
        info = scrapertools.find_single_match(data, "<quality>(.*?)</quality>")
        if info:
            patron = "<item>(.*?)</item>"
            matches = re.compile(patron, re.DOTALL).findall(info)
            for value in matches:
                list_quality.append(value)

        channel_parameters["list_quality"] = list_quality

        logger.info("pelisalacarta.core.channeltools get_channel_parameters channel_parameters={chn}".
                    format(chn=channel_parameters))

    else:
        logger.info("pelisalacarta.core.channeltools get_channel_parameters "+channel_name+".xml NOT found")

        channel_parameters = dict()
        channel_parameters["adult"] = "false"

    return channel_parameters
