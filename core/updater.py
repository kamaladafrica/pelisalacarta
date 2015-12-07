# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta
# XBMC Plugin
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import scrapertools
import time
import config
import logger
import traceback
from core import channeltools
from core import jsontools
from platformcode import guitools
from distutils.version import StrictVersion

repo = channeltools.repo
branch = channeltools.branch

GitApi = "https://api.github.com/repos/"+repo+"/contents/python/main-classic/channels?ref="+branch

def GetDownloadPath(version, platform=""):
    zipfile = config.PLUGIN_NAME + "-%s-%s.zip"
    if not platform:
        if config.PLATFORM_NAME=="kodi-isengard":
            platform = "kodi-isengard"
        elif config.PLATFORM_NAME=="kodi-helix":
            platform = "kodi-helix"
        elif config.PLATFORM_NAME=="xbmceden":
            platform = "xbmc-eden"
        elif config.PLATFORM_NAME=="xbmcfrodo":
            platform = "xbmc-frodo"
        elif config.PLATFORM_NAME=="xbmcgotham":
            platform = "xbmc-gotham"
        elif config.PLATFORM_NAME=="xbmc":
            platform = "xbmc-plugin"
        elif config.PLATFORM_NAME=="wiimc":
            platform = "wiimc"
        elif config.PLATFORM_NAME=="rss":
            platform = "rss"
        else:
            platform = config.PLATFORM_NAME
    return zipfile % (platform, version)    
    
def Threaded_checkforupdates():
    if config.get_setting("updatecheck2") == "true": 
        #Actualizaciones del plugin
        logger.info("pelisalacarta.core.updater Threaded_checkforupdates")
        REMOTE_VERSION_FILE = "http://descargas.tvalacarta.info/"+config.PLUGIN_NAME+"-version.xml"
        # Descarga el fichero con la versión en la web
        logger.info("pelisalacarta.core.updater Verificando actualizaciones...")
        logger.info("pelisalacarta.core.updater Version remota: "+REMOTE_VERSION_FILE)
        data = scrapertools.cachePage( REMOTE_VERSION_FILE )

        '''    
            <?xml version="1.0" encoding="utf-8" standalone="yes"?>
            <version>
                    <name>pelisalacarta</name>
                    <tag>4.0     </tag>
                    <version>4000</tag>
                    <date>20/03/2015</date>
                    <changes>New release</changes>
            </version>
        '''
        #version_publicada = scrapertools.find_single_match(data,"<tag>([^<]+)</tag>").strip()
        version_publicada = scrapertools.find_single_match(data,"<version>([^<]+)</version>").strip()
        if not version_publicada:
            # Mantenemos por retrocompatibilidad con v < 4.0
            version_publicada = scrapertools.find_single_match(data,"<tag>([^<]+)</tag>").strip()
        
        version_remota= (version_publicada + '.0') if version_publicada.find('.') == -1 else version_publicada
        logger.info("pelisalacarta.core.updater version remota=" + version_remota)
        
        # Lee el fichero con la versión instalada
        localFileName = os.path.join( config.get_runtime_path() , "version.xml" )
        logger.info("pelisalacarta.core.updater fichero local version: "+localFileName)
        infile = open( localFileName )
        data = infile.read()
        infile.close();

        #version_local = scrapertools.find_single_match(data,"<tag>([^<]+)</tag>").strip()
        version_local = scrapertools.find_single_match(data,"<version>([^<]+)</version>").strip()
        if not version_local:
            version_local = scrapertools.find_single_match(data,"<tag>([^<]+)</tag>").strip()
            
        if version_local.find('.') == -1: version_local += '.0'
        logger.info("pelisalacarta.core.updater version local=" +version_local)
            
        if StrictVersion(version_remota) > StrictVersion(version_local):
            if guitools.dialog_yesno( "Versión "+version_remota+" disponible" , "¿Quieres instalarla?" ):
                update_plugin(version_publicada)
                return
    
    if config.get_setting("when_oficial_updatechannels") == '0': # == Nunca
        return
    
    try:
        headers = {'Accept': 'application/json'}
        request = urllib2.Request(GitApi , headers=headers)
        response_body = urllib2.urlopen(request).read()
    except:
        logger.info("pelisalacarta.core.updater Threaded_checkforupdates: Error get api.github")
        logger.info(traceback.format_exc())
        return None
        
    list_channelsJSON_locales = channeltools.get_list_channels_json()    
    list_channelsJSON_remote = jsontools.load_json(response_body)
    list_channels_remoto=[]
    update = None
    down = None
    save =False
    
    for c in list_channelsJSON_remote:
        channel_name= os.path.splitext(c['name'])[0]
        if c['name'].endswith('.py') and not c['name'].startswith('_'):
            list_channels_remoto.append(channel_name)

            if config.get_setting("add_oficial_updatechannels") == 'true' and not os.path.exists(channeltools.get_channel_local_path(channel_name)+'.py'):
                # Añadir canales nuevos
                remote_channel_url = channeltools.get_channel_remote_url(channel_name)
                down = channeltools.download_channel(channel_name, remote_channel_url)
                if down:
                    list_channelsJSON_locales[channel_name] = down
                    save = True
                    logger.info("pelisalacarta.core.updater Threaded_checkforupdates: Añadido canal " + down['name'])
                    guitools.dialog_notification("Actualizaciones automaticas", "Añadido canal " + down['name'],time=2500)
    
    for ChannelId, ChannelData in list_channelsJSON_locales.items():
        if not ChannelData['update_url']:
            # Canal oficial
            if not ChannelId in list_channels_remoto: 
                #  Ya no esta en el repositorio
                if config.get_setting("del_oficial_updatechannels") == '1': # == Ocultar
                    list_channelsJSON_locales[ChannelId]['status'] =  'desactivado'
                    save = True
                elif config.get_setting("del_oficial_updatechannels") == '2': # == Eliminar
                    list_channelsJSON_locales[ChannelId]['status'] =  'borrable'
                    save = True
            
            if config.get_setting("when_oficial_updatechannels") == '1': # == Al inicio
                update = channeltools.updatechannel(ChannelId, ChannelData['version'])
                if update:
                    list_channelsJSON_locales[ChannelId] = update
                    logger.info("pelisalacarta.core.updater Threaded_checkforupdates: Actualizado canal " + ChannelData['name'])
                    guitools.dialog_notification("Actualizaciones automaticas", "Actualizado canal " + ChannelData['name'],time=2500)
        elif config.get_setting("when_unoficial_updatechannels") == '1' and config.get_setting("when_oficial_updatechannels") == '1': # == 'Como los oficiales' y oficiales == 'al inicio'
            # Canal no oficial
            update = channeltools.updatechannel(ChannelId, ChannelData['version'], ChannelData['update_url'])
            if update:
                list_channelsJSON_locales[ChannelId] = update
                save = True
                logger.info("pelisalacarta.core.updater Threaded_checkforupdates: Actualizado canal " + ChannelData['name'])
                guitools.dialog_notification("Actualizaciones automaticas", "Actualizado canal " + ChannelData['name'],time=2500)
            
    
    if save:
        channeltools.set_list_channels_json(list_channelsJSON_locales)
    
    #guitools.dialog_ok("Actualizaciones automaticas", "Fin") # Eliminar

def update_plugin(version):
    # Descarga el ZIP
    logger.info("pelisalacarta.core.updater update")
    remotefilename =  "http://descargas.tvalacarta.info/" + GetDownloadPath(version)
    localfilename = os.path.join( config.get_data_path(), config.PLUGIN_NAME + "-" + version + ".zip" )
    logger.info("pelisalacarta.core.updater remotefilename=%s" % remotefilename)
    logger.info("pelisalacarta.core.updater localfilename=%s" % localfilename)
    logger.info("pelisalacarta.core.updater descarga fichero...")
    inicio = time.clock()
    
    #urllib.urlretrieve(remotefilename,localfilename)
    from core import downloadtools
    ret = downloadtools.downloadfile(remotefilename, localfilename, continuar=False)
    
    fin = time.clock()
    logger.info("pelisalacarta.core.updater Descargado en %d segundos " % (fin-inicio+1))
    
    if ret is None:
        # Lo descomprime
        logger.info("pelisalacarta.core.updater descomprime fichero...")
        import ziptools
        unzipper = ziptools.ziptools()
        #destpathname = DESTINATION_FOLDER
        destpathname =  os.path.join(config.get_runtime_path(),"..")
        logger.info("pelisalacarta.core.updater destpathname=%s" % destpathname)
        unzipper.extract(localfilename,destpathname)
        
        # Borra el zip descargado
        logger.info("pelisalacarta.core.updater borra fichero...")
        os.remove(localfilename)
        logger.info("pelisalacarta.core.updater ...fichero borrado")
        guitools.dialog_ok ("Actualizacion", "Pelisalacarta se ha actualizado correctamente")

    elif ret == -1:
        # Descarga Cancelada
        guitools.dialog_ok ("Actualizacion", "Descarga Cancelada")
    else:
        # Error en la descarga
        guitools.dialog_ok ("Actualizacion", "Se ha producido un error al descargar el archivo")
        


