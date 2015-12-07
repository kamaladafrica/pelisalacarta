# -*- coding: utf-8 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
#------------------------------------------------------------
# channeltools
# Herramientas para trabajar con canales
#------------------------------------------------------------
import urllib2
import urlparse
import io
import os,sys,re,traceback
import config
import logger
import scrapertools
import codecs
from core import jsontools
from distutils.version import StrictVersion

'''
repo = "superberny70/pelisalacarta"
branch = "feature_xml2json"
'''
repo = "tvalacarta/pelisalacarta"
branch = "master"
GitUrl = "https://raw.githubusercontent.com/" + repo +"/" + branch + "/python/main-classic/"

 
def get_channel_properties(file_path):
    ''' Obtiene las propiedades del canal.
    
    Abre el archivo de propiedades y devuelve una objeto tipo JSON con los datos obtenidos.
    El archivo de propiedades es un JSON y esta localizado en la ruta o url especificada por el parametro file_path.
        
    Parametros: 
    (string) file_path: ruta local o url al fichero .json del canal a consultar.
       
    Retorna:
    Un objeto JSON con como mimimo los siguientes campos:
            {'name' : channel.name,
            'version' : channel.version, 
            'update_url' : channel.update_url,
            'active' : False
            }
        -(string) channel.name: Nombre del canal.
        -(string) channel.version: La version del canal en formato X.Y[.Z] siendo Z opcional. 
                  Si esta informacion no esta en el archivo retorna '0.0.0'
        -(string) channel.update_url: Url incluida en el archivo de propiedades desde 
                  la cual descargar el canal. 
                  Si esta informacion no esta en el archivo retorna una cadena vacia.
    
    '''
    
    ret = {'channel':{
                      'name' : os.path.splitext(os.path.basename(file_path))[0].capitalize(),
                      'version' : '0.0.0', 
                      'update_url' : "",
                      'active' : False
                      }
          }
          
    if os.path.exists(file_path):
        # Fichero local JSON
        infile = open(file_path)
        file_version_data= jsontools.load_json(infile.read())
        infile.close()
    else:
        # Fichero remoto JSON
        try:
            infile = urllib2.urlopen(file_path,'rU')
            file_version_data = jsontools.load_json(infile.read())
        except:
            import sys
            for line in sys.exc_info():
                logger.error( "%s" % line )
            return ret
         
    if file_version_data['channel']['version'].find('.') == -1: 
        file_version_data['channel']['version'] += '.0'
    ret = file_version_data
                
    return ret['channel']
    
def get_channel_remote_url(channel_name, update_url = None):
    ''' Devuelve la url de donde se ha de descargar el canal.
    
    Devuelve la url base de donde descargar los archivos .py y .json
    del canal cuyo nombre pasamos como parametro. Esta url termina
    precisamente con el nombre del canal.
        
    Parametros: 
    (string) channel_name: nombre del canal
    (string) update_url: (Opcional) direccion url del canal en el caso 
    de que no sea del repositorio por defecto. 
   
    Retorna:
    (string) La direccion url base al archivo remoto canal.py 
    sin la extension. El resto de archivos del canal deben compartir 
    la misma url base.
    
    '''
    
    if channel_name == "channelselector":
        remote_channel_url = GitUrl + channel_name
    elif not update_url:
        # Repositorio por defecto 
        remote_channel_url = GitUrl + 'channels/' + channel_name
    else:
        # Repositorio especifico
        if update_url.endswith('.py'):
            update_url= update_url[:-3]
        elif update_url.endswith('.json'):
            update_url= update_url[:-5]
        elif update_url.endswith('/'):
            update_url= update_url[:-1]
        
        if not update_url.endswith('/' + channel_name):
            update_url += '/' +channel_name
            
        remote_channel_url = update_url
        
    logger.info("pelisalacarta.core.channeltools remote_channel_url="+remote_channel_url)

    return remote_channel_url 

def get_channel_local_path(channel_name):
    ''' Devuelve la ruta donde se ha guarda el canal.
    
    Devuelve la ruta base de donde se guardan los archivos .py y .json
    del canal cuyo nombre pasamos como parametro. Esta ruta termina
    precisamente con el nombre del canal.
        
    Parametros: 
    (string) channel_name: nombre del canal
       
    Retorna:
    (string) La ruta base al archivo canal.py sin la extension. 
    
    '''

    if channel_name == "channelselector":
        local_channel_path = os.path.join( config.get_runtime_path() , channel_name)
    else:
         local_channel_path = os.path.join( config.get_runtime_path() , 'channels' , channel_name)
    logger.info("pelisalacarta.core.channeltools local_channel_path="+local_channel_path)

    return local_channel_path

def updatechannel(channel_name, local_version="",  update_url=""):
    ''' Determina si se ha de actualizar el canal pasado como parametro.
    
    En funcion de la version incluida en el archivo local de propiedades
    del canal y de la version del archivo remoto de propiedades del mismo canal,
    descargara el canal. Es decir, si la version remota es superior a la version local, 
    se descargara el canal en otro caso no.
    
    Parametros: 
    (string) channel_name: nombre del canal
    (string) local_version (opcional): Version del canal instalado localmente en formato X.Y[.Z]
    (string) update_url (opcional): Direccion url desde donde actualizar el canal en caso necesario
    
    Retorna:
    (dict) En caso de que el canal haya sido actualizado, retorna un diccionario con parametros del canal. En caso contrario retorna None
    
    '''

    logger.info("pelisalacarta.core.channeltools updatechannel('"+channel_name+"')")
    
    # Canal local
    if not local_version:
        local_channel_path = get_channel_local_path(channel_name) 
        channel_local_properties = get_channel_properties(local_channel_path + '.json')
        local_version = channel_local_properties['version']
        update_url = channel_local_properties['update_url']
    logger.info("pelisalacarta.core.channeltools local_version=%s" % local_version)
    
    # Canal remoto
    remote_channel_url = get_channel_remote_url(channel_name, update_url)
    remote_version = get_channel_properties(remote_channel_url + '.json')['version']
    logger.info("pelisalacarta.core.channeltools remote_version=%s" % remote_version)

    # Comprueba si ha cambiado
    if StrictVersion(remote_version) > StrictVersion(local_version):
        ret = download_channel(channel_name, remote_channel_url)
        if ret:
            logger.info("pelisalacarta.core.channeltools updated")
            return ret
            
    return None
  
def download_channel(channel_name, remote_channel_url):
    ''' Descarga un canal.
    
    Descarga el canal cuyo nombre se pasan como primer parametro desde la url
    del segundo parametro.
    
    Parametros: 
    
        
    Retorno:
    (dict) En caso de que el canal haya sido descargado, retorna un diccionario con parametros del canal. En caso contrario retorna None
    
    '''
    logger.info("pelisalacarta.core.channeltools download_channel('"+channel_name+"')")
    local_channel_path = get_channel_local_path(channel_name)
        
    try:
        if os.path.exists(local_channel_path + ".pyo"):
            os.remove(local_channel_path + ".pyo")
        for ext in [".py", ".json"]:
            updated_channel_data =urllib2.urlopen(remote_channel_url + ext,'rU').read()
            outfile = file(local_channel_path + ext ,"w")
            outfile.write(updated_channel_data)
            outfile.close()
            logger.info("pelisalacarta.core.channeltools Grabado a " + local_channel_path + ext)
            
        channel_json = jsontools.load_json(updated_channel_data)['channel']
        return {"adult": channel_json['adult'], 
                "category": channel_json['category'], 
                "fanart": channel_json['fanart'], 
                "include_in_global_search": channel_json['include_in_global_search'], 
                "language": channel_json['language'], 
                "status": 'activado' if channel_json['active'] else 'desactivado', 
                "thumbnail": channel_json['thumbnail'], 
                "name": channel_json['name'],
                "update_url": channel_json['update_url']
                }
         
    except:
        logger.info("pelisalacarta.core.channeltools Error al grabar " + local_channel_path + ext)
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return None
        
    return True
   
def get_list_channels_json():
    ''' Retorna el contenido del archivo indice de canales.
      
    Retorno:
    (obj JSON) Lista ordenada de canales instalados localmente con sus parametros principales.
    '''     
    file_path= os.path.join(config.get_data_path(),"list_channels.json")
    if os.path.exists(file_path):
        infile = open(file_path)
        list_channels_json = jsontools.load_json(infile.read())
        infile.close()
    else:
        list_channels_json = None
        
    return list_channels_json
 		
def set_list_channels_json(data_json = {}):
    ''' Guarda el contenido de data_json. 

    El contenido del parametro de entrada es guardado en el fichero 
    'userdata\addon_data\plugin.video.pelisalacarta\list_channels.json'
    
    Parametro:
    (obj JSON) data_json:(opcional) Propiedades del canal. Habitualmente el objeto devuelto por 
    get_channel_properties(). Si no se pasa nada creara la lista recorriendo el directorio de canales.
    
    Retorno:
    (obj JSON) Si el parametro data_json existia retorna este mismo dato, pero si no existia retorna el 
    contenido de la lista recien creada. En caso de error retorna None.
    '''
    
    file_path= os.path.join(config.get_data_path(),"list_channels.json")
    if not data_json:
        logger.info("pelisalacarta.core.channeltools Creando list_channels.json ...")
        local_chanels_path = os.path.join( config.get_runtime_path(), 'channels')
        list_chanelsJSON_locales= [os.path.join(local_chanels_path,c) for c in os.listdir(local_chanels_path) if c.endswith('.json') and not c.startswith('_')]

        for channel in list_chanelsJSON_locales:
            channel_json =  get_channel_properties(channel)
            data_json[channel_json['id']] = {"adult": channel_json['adult'], 
                                             "category": channel_json['category'], 
                                             "fanart": channel_json['fanart'], 
                                             "include_in_global_search": channel_json['include_in_global_search'], 
                                             "language": channel_json['language'], 
                                             "status": 'activado' if channel_json['active'] else 'desactivado', 
                                             "thumbnail": channel_json['thumbnail'], 
                                             "name": channel_json['name'],
                                             "update_url": channel_json['update_url'],
                                             "version": channel_json['version'] if channel_json['version'].find('.') > 0 else channel_json['version'] + '.0'
                                             }
                                             
    # Guardamos en list_channels.json
    try:
        with io.open(file_path, "w", encoding="utf-8") as f:
            f.write(jsontools.dump_json(data_json).decode('utf-8'))
    except:
        data_json = None
        
    return data_json

