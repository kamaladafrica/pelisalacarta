# -*- coding: utf-8 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
#------------------------------------------------------------
# channeltools
# Herramientas para trabajar con canales
#------------------------------------------------------------

import os,sys,re,traceback

import config
import logger
import scrapertools
import jsontools

def is_adult(channel_name):
    logger.info("pelisalacarta.core.channeltools is_adult channel_name="+channel_name)

    channel_parameters = get_channel_parameters(channel_name)

    return channel_parameters["adult"]=="true"

def get_channel_parameters(channel_name):
    logger.info("pelisalacarta.core.channeltools get_channel_parameters channel_name="+channel_name)

    channel_xml = os.path.join( config.get_runtime_path() , 'channels' , channel_name+".xml" )

    if os.path.exists(channel_xml):
        logger.info("pelisalacarta.core.channeltools get_channel_parameters "+channel_name+".xml found")

        infile = open( channel_xml , "rb" )
        data = infile.read()
        infile.close();

        # TODO: Pendiente del json :)
        channel_parameters = {}
        channel_parameters["title"] = scrapertools.find_single_match(data,"<name>([^<]*)</name>")
        channel_parameters["channel"] = scrapertools.find_single_match(data,"<id>([^<]*)</id>")
        channel_parameters["active"] = scrapertools.find_single_match(data,"<active>([^<]*)</active>")
        channel_parameters["adult"] = scrapertools.find_single_match(data,"<adult>([^<]*)</adult>")
        channel_parameters["language"] = scrapertools.find_single_match(data,"<language>([^<]*)</language>")
        channel_parameters["thumbnail"] = scrapertools.find_single_match(data,"<thumbnail>([^<]*)</thumbnail>")
        channel_parameters["bannermenu"] = scrapertools.find_single_match(data,"<bannermenu>([^<]*)</bannermenu>")
        channel_parameters["fanart"] = scrapertools.find_single_match(data,"<fanart>([^<]*)</fanart>")
        channel_parameters["include_in_global_search"] = scrapertools.find_single_match(data,"<include_in_global_search>([^<]*)</include_in_global_search>")
        channel_parameters["type"] = "generic"

        category_list = []
        matches = scrapertools.find_multiple_matches(data, "<category>([^<]*)</category>")
        for match in matches:
            category_list.append(match)

        channel_parameters["categories"] = category_list

        logger.info("pelisalacarta.core.channeltools get_channel_parameters channel_parameters="+repr(channel_parameters) )

    else:
        logger.info("pelisalacarta.core.channeltools get_channel_parameters "+channel_name+".xml NOT found")

        channel_parameters = {}
        channel_parameters["adult"] = "false"

    return channel_parameters

def get_channel_json(channel_name):
    logger.info("pelisalacarta.core.channeltools get_channel_json channel_name="+channel_name)
    channel_xml =os.path.join(config.get_runtime_path() , 'channels' , channel_name + ".xml")
    channel_json = jsontools.xmlTojson(channel_xml)
    return channel_json['channel']
    
def get_channel_controls_settings(channel_name):    
    logger.info("pelisalacarta.core.channeltools get_channel_controls_settings channel_name="+channel_name)
    dict_settings= {}
    
    settings= get_channel_json(channel_name)['settings']
    if type(settings) == list:
        list_controls = settings
    else:
        list_controls.append(settings)
        
    # Conversion de str a bool, etc...
    for c in list_controls:
        if not c.has_key('id') or not c.has_key('type') or not c.has_key('default'):
            # Si algun control de la lista  no tiene id, type o default lo ignoramos
            continue
        if not c.has_key('enabled') or c['enabled'] is None: 
            c['enabled']= True
        else:
            c['enabled'] = True if c['enabled'].lower() == "true" else False
        if not c.has_key('visible') or c['visible'] is None: 
            c['visible']= True
        else:
            c['visible'] = True if c['visible'].lower() == "true" else False
        if c['type'] == 'bool':
            c['default'] = True if c['default'].lower() == "true" else False
        dict_settings[c['id']] = c['default']
    
    return list_controls, dict_settings
                        