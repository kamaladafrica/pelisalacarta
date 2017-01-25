# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para Pepecine
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import ast
import re
import sys
import urlparse

from core import config
from core import jsontools
from core import logger
from core import scrapertools
from core import httptools
from core import servertools
from core.item import Item, InfoLabels


__url_base__ = "http://pepecine.net"
__chanel__ = "pepecine"
fanart_host = "https://d12.usercdn.com/i/02278/u875vjx9c0xs.png"


def mainlist(item):
    logger.info()

    itemlist = []
    url_peliculas = urlparse.urljoin(__url_base__,"plugins/ultimas-peliculas-updated.php")
    itemlist.append( Item(channel=__chanel__, title="Películas", text_color="0xFFEB7600", text_blod=True, fanart=fanart_host,
                          thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/movies.png"))
    itemlist.append(Item(channel=__chanel__, action="listado", title="     Novedades", page=0, viewcontent = "movies",
                         text_color="0xFFEB7600", extra="movie", fanart=fanart_host, url=url_peliculas,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/movies.png"))
    itemlist.append( Item(channel=__chanel__, action="sub_filtrar", title="     Filtrar películas por género",
                          text_color="0xFFEB7600", extra="movie", fanart=fanart_host, url= url_peliculas,
                          thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/movies_filtrar.png"))
    itemlist.append( Item(channel=__chanel__, action="search", title="     Buscar películas por título",
                          text_color="0xFFEB7600", extra="movie", fanart=fanart_host, url= url_peliculas,
                          thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/movies_buscar.png"))

    url_series = urlparse.urljoin(__url_base__, "plugins/series-episodios-updated.php")
    itemlist.append( Item(channel=__chanel__, title="Series", text_color="0xFFEB7600", text_blod=True, fanart=fanart_host,
                          thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/tv.png"))
    itemlist.append(Item(channel=__chanel__, action="listado", title="     Novedades", page=0, viewcontent = "tvshows",
                         text_color="0xFFEB7600", extra="series", fanart=fanart_host, url=url_series,
                         thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/tv.png"))
    itemlist.append( Item(channel=__chanel__, action="sub_filtrar", title="     Filtrar series por género",
                          text_color="0xFFEB7600", extra="series", fanart=fanart_host, url= url_series,
                          thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/tv_filtrar.png"))
    itemlist.append( Item(channel=__chanel__, action="search", title="     Buscar series por título",
                          text_color="0xFFEB7600", extra="series", fanart=fanart_host, url= url_series,
                          thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/tv_buscar.png"))
    itemlist.append( Item(channel=__chanel__, action="listado", title="     Ultimos episodios actualizados",
                          text_color="0xFFEB7600", extra="series_novedades", fanart=fanart_host,
                          url= urlparse.urljoin(__url_base__, "plugins/ultimos-capitulos-updated.php"),
                          thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/tv.png"))
    
    return itemlist
 
def sub_filtrar(item):
    logger.info()
    itemlist=[]
    generos=("acción","animación","aventura","ciencia ficción","comedia","crimen",
             "documental","drama","familia","fantasía","guerra","historia","misterio",
             "música","musical","romance","terror","thriller","western")
    thumbnail=('https://d12.usercdn.com/i/02278/spvnq8hghtok.jpg',
               'https://d12.usercdn.com/i/02278/olhbpe7phjas.jpg',
               'https://d12.usercdn.com/i/02278/8xm23q2vewtt.jpg',
               'https://d12.usercdn.com/i/02278/o4vuvd7q4bau.jpg',
               'https://d12.usercdn.com/i/02278/v7xq7k9bj3dh.jpg',
               'https://d12.usercdn.com/i/02278/yo5uj9ff7jmg.jpg',
               'https://d12.usercdn.com/i/02278/ipeodwh6vw6t.jpg',
               'https://d12.usercdn.com/i/02278/0c0ra1wb11ro.jpg',
               'https://d12.usercdn.com/i/02278/zn85t6f2oxdv.jpg',
               'https://d12.usercdn.com/i/02278/ipk94gsdqzwa.jpg',
               'https://d12.usercdn.com/i/02278/z5hsi6fr4yri.jpg',
               'https://d12.usercdn.com/i/02278/nq0jvyp7vlb9.jpg',
               'https://d12.usercdn.com/i/02278/tkbe7p3rjmps.jpg',
               'https://d12.usercdn.com/i/02278/is60ge4zv1ve.jpg',
               'https://d12.usercdn.com/i/02278/86ubk310hgn8.jpg',
               'https://d12.usercdn.com/i/02278/ph1gfpgtljf7.jpg',
               'https://d12.usercdn.com/i/02278/bzp3t2edgorg.jpg',
               'https://d12.usercdn.com/i/02278/31i1xkd8m30b.jpg',
               'https://d12.usercdn.com/i/02278/af05ulgs20uf.jpg')

    if item.extra == "movie":
        viewcontent = "movies"
    else:
        viewcontent = "tvshows"


    for g, t in zip(generos,thumbnail):
        itemlist.append(item.clone(action="listado", title= g.capitalize(),filtro=("genero",g),thumbnail=t,
                                   viewcontent=viewcontent ))
   
    return itemlist 

def search(item,texto):
    logger.info("search:" + texto)
    #texto = texto.replace(" ", "+")
    item.filtro=("search",texto.lower())
    try:
        return listado(item) 
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def newest(categoria):
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = urlparse.urljoin(__url_base__,"plugins/ultimas-peliculas-updated.php")
            item.extra = "movie"

        elif categoria == 'infantiles':
            item.url = urlparse.urljoin(__url_base__, "plugins/ultimas-peliculas-updated.php")
            item.filtro=("genero","animación")
            item.extra = "movie"

        elif categoria == 'series':
            item.url = urlparse.urljoin(__url_base__,"plugins/ultimos-capitulos-updated.php")
            item.extra="series_novedades"

        else:
            return []

        itemlist = listado(item)
        if itemlist[-1].action == "listado":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def listado(item):
    logger.info()
    itemlist = []

    try:
        data_dict = jsontools.load_json(httptools.downloadpage(item.url).data)
    except:
        return itemlist # Devolvemos lista vacia

    #Filtrado y busqueda
    if item.filtro:
        for i in data_dict["result"][:]:
            if (item.filtro[0] == "genero" and item.filtro[1] not in i['genre'].lower()) or \
                (item.filtro[0] == "search" and item.filtro[1] not in i['title'].lower()):
                    data_dict["result"].remove(i)


    if not item.page:
        item.page = 0

    offset= int(item.page) * 60
    limit= offset + 60
       
    for i in data_dict["result"][offset:limit]:
        infoLabels = InfoLabels()
        idioma = ''

        if item.extra == "movie":
            action= "get_movie"
            #viewcontent = 'movies'
            infoLabels["title"]= i["title"]
            title= '%s (%s)' % (i["title"], i['year'] )
            url= urlparse.urljoin(__url_base__,"ver-pelicula-online/" + str(i["id"]))

        elif item.extra=="series": 
            action="get_temporadas"
            #viewcontent = 'seasons'
            title= i["title"]
            infoLabels['tvshowtitle']= i["title"]
            url= urlparse.urljoin(__url_base__,"episodio-online/" + str(i["id"]))

        else: #item.extra=="series_novedades": 
            action="get_only_episodio"
            #viewcontent = 'episodes'
            infoLabels['season']=i['season']
            infoLabels['episode']=i['episode'].zfill(2)
            item.extra= "%sx%s" %(infoLabels["season"], infoLabels["episode"])
            infoLabels['tvshowtitle']= i["title"]
            flag= scrapertools.find_single_match(i["label"],'(\s*\<img src=.*\>)')
            idioma=i["label"].replace(flag,"")
            title = '%s %s (%s)' %(i["title"], item.extra, idioma)
            url= urlparse.urljoin(__url_base__,"episodio-online/" + str(i["id"]))
        
        if i.has_key("poster") and i["poster"]: 
            thumbnail=re.compile("/w\d{3}/").sub("/w500/",i["poster"])
        else:
            thumbnail= item.thumbnail
        if i.has_key("background") and i["background"]: 
            fanart= i["background"]
        else:
            fanart= item.fanart
        
        # Rellenamos el diccionario de infoLabels
        infoLabels['title_id']=i['id'] # title_id: identificador de la pelicula/serie en pepecine.com
        infoLabels['titleraw']= i["title"] # titleraw: titulo de la pelicula/serie sin formato
        if i['genre']: infoLabels['genre']=i['genre']
        if i['year']: infoLabels['year']=i['year']
        if i['tagline']: infoLabels['plotoutline']=i['tagline']
        if i['plot']: 
            infoLabels['plot']=i['plot']
        else:
            infoLabels['plot']=""
        if i['runtime']: infoLabels['duration']=int(i['runtime'])*60
        if i['imdb_rating']:
            infoLabels['rating']=i['imdb_rating']
        elif i['tmdb_rating']:
            infoLabels['rating']=i['tmdb_rating']
        if i['tmdb_id']: infoLabels['tmdb_id'] = i['tmdb_id']
        if i['imdb_id']: infoLabels['imdb_id'] = i['imdb_id']



        newItem = Item(channel=item.channel, action=action, title=title, url=url, extra=item.extra,
                         fanart=fanart, thumbnail=thumbnail, viewmode="movie_with_plot", #viewcontent=viewcontent,
                         language=idioma, text_color="0xFFFFCE9C", infoLabels=infoLabels)
        newItem.year=i['year']
        newItem.contentTitle=i['title']
        if 'season' in infoLabels and infoLabels['season']:
            newItem.contentSeason = infoLabels['season']
        if 'episode' in infoLabels and infoLabels['episode']:
            newItem.contentEpisodeNumber = infoLabels['episode']
        itemlist.append(newItem)
    
    # Paginacion
    if len(data_dict["result"]) > limit:
        itemlist.append(item.clone(text_color="0xFF994D00", title=">> Pagina siguiente >>", page=item.page + 1) )
    
    return itemlist      
              
def get_movie(item):
    logger.info()
    itemlist = []
    #logger.debug(item)

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)","",httptools.downloadpage(item.url).data)
    patron ='vars.title =(.*?)};'
    try:
        data_dict= jsontools.load_json(scrapertools.get_match(data,patron) +'}')
    except:
        return itemlist # Devolvemos lista vacia
    
    infoLabels=item.infoLabels
    if data_dict.has_key("actor"):
        cast=[]
        rol=[]
        for actor in data_dict["actor"]:
            cast.append(actor['name'])
            rol.append(actor['pivot']['char_name'])
        infoLabels['cast'] = cast
        infoLabels['castandrole'] = zip(cast,rol)
        
    if data_dict.has_key("writer"):
        writers_list=[]
        for writer in data_dict["writer"]:
            writers_list.append(writer['name'])
        infoLabels['writer'] = ", ".join(writers_list )
        
    if data_dict.has_key("director"):    
        director_list=[]
        for director in data_dict["director"]:
            director_list.append(director['name'])    
        infoLabels['director'] = ", ".join(director_list )
    

    item.infoLabels= infoLabels
    item.url=str(data_dict["link"])
    #logger.debug(item)
    itemlist = findvideos (item)

    if config.get_library_support() and itemlist:
        infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                      'title': item.infoLabels['title']}
        itemlist.append(Item(channel=item.channel, title="Añadir esta película a la biblioteca",text_color="0xFFe5ffcc",
                             action ="add_pelicula_to_library",infoLabels=infoLabels, contentType='movie', url=item.url,
                             thumbnail=item.thumbnail ))

    return itemlist
    
def get_temporadas(item):
    logger.info()

    itemlist = []
    infoLabels = {}


    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)","",httptools.downloadpage(item.url).data)
    patron ='vars.title =(.*?)};'
    try:
        data_dict= jsontools.load_json(scrapertools.get_match(data,patron) +'}')
    except:
        return itemlist # Devolvemos lista vacia
    
    if item.extra == "serie_add":
        item.extra=str(data_dict['tmdb_id'])
        item.url=str(data_dict["link"])
        infoLabels['titleraw'] = data_dict["title"]
        infoLabels['tvshowtitle'] = data_dict["title"]
        infoLabels['title_id'] = data_dict['id']
        item.infoLabels = infoLabels
        itemlist= get_episodios(item)
    else:
        infoLabels = item.infoLabels
        if data_dict.has_key("actor"):
            cast=[]
            rol=[]
            for actor in data_dict["actor"]:
                cast.append(actor['name'])
                rol.append(actor['pivot']['char_name'])
            infoLabels['cast'] = cast
            infoLabels['castandrole'] = zip(cast,rol)
            
        if data_dict.has_key("writer"):    
            writers_list=[]
            for writer in data_dict["writer"]:
                writers_list.append(writer['name'])
            infoLabels['writer'] = ", ".join(writers_list )
        
        if data_dict.has_key("director"):  
            director_list=[]
            for director in data_dict["director"]:
                director_list.append(director['name'])    
            infoLabels['director'] = ", ".join(director_list )
    
        if len(data_dict["season"]) == 1: 
            # Si solo hay una temporada ...
            item.extra=str(data_dict['tmdb_id'])
            item.url=str(data_dict["link"])
            item.infoLabels = infoLabels
            itemlist= get_episodios(item)
        else: #... o si hay mas de una temporada y queremos el listado por temporada...
            item.extra=str(data_dict['tmdb_id'])
            item.viewcontent = "seasons"
            data_dict["season"].sort(key=lambda x:(x['number'])) # ordenamos por numero de temporada
            for season in data_dict["season"]:
                url= filter(lambda l: l["season"]== season['number'],data_dict["link"]) #filtramos enlaces por temporada
                if url:
                    if season['overview']: infoLabels['plot']=season['overview']
                    if season['number']: infoLabels['season']=season['number']
                    if season["poster"]: item.thumbnail=re.compile("/w\d{3}/").sub("/w500/",season["poster"])
                    if season["release_date"]: infoLabels['premiered']= season['release_date']

                    item.infoLabels = infoLabels
                    title=item.title + ' ' + season["title"].lower().replace('season','temporada').capitalize()
                    
                    itemlist.append( Item( channel=item.channel, action="get_episodios", title=title, url=str(url),
                                           extra=item.extra, fanart=item.fanart, text_color="0xFFFFCE9C",
                                           thumbnail=item.thumbnail, viewmode="movie_with_plot",
                                           infoLabels=item.infoLabels) )
            
            if config.get_library_support() and itemlist:
                url= urlparse.urljoin(__url_base__,"episodio-online/" + str(data_dict['id']))
                itemlist.append( Item(channel=item.channel,
                                      title="Añadir esta serie a la biblioteca", url=url,
                                      action="add_serie_to_library", extra='episodios###serie_add',
                                      show= data_dict["title"], text_color="0xFFe5ffcc",
                                      thumbnail = 'https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/tv.png'))

    return itemlist      

def get_only_episodio(item):
    logger.info()
    itemlist = []
    plot={}
    
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)","",httptools.downloadpage(item.url).data)
    patron ='vars.title =(.*?)};'
    try:
        data_dict= jsontools.load_json(scrapertools.get_match(data,patron) +'}')
    except:
        return itemlist # Devolvemos lista vacia
        
    try:
        from core.tmdb import Tmdb
        oTmdb= Tmdb(id_Tmdb= data_dict['tmdb_id'],tipo="tv")
    except:
        pass

    infoLabels = item.infoLabels
    if data_dict.has_key("actor"):
        cast=[]
        rol=[]
        for actor in data_dict["actor"]:
            cast.append(actor['name'])
            rol.append(actor['pivot']['char_name'])
        infoLabels['cast'] = cast
        infoLabels['castandrole'] = zip(cast, rol)

    if data_dict.has_key("actor"):
        writers_list=[]
        for writer in data_dict["writer"]:
            writers_list.append(writer['name'])
        infoLabels['writer'] = ", ".join(writers_list)

    if data_dict.has_key("actor"):
        director_list=[]
        for director in data_dict["director"]:
            director_list.append(director['name'])
        infoLabels['director'] = ", ".join(director_list)


    infoLabels['season'], infoLabels['episode']= item.extra.split('x')
    try:
        # añadimos sinopsis e imagenes del capitulo
        datos_tmdb=oTmdb.get_episodio(temporada= infoLabels['season'],capitulo= infoLabels['episode'])
        if datos_tmdb["episodio_sinopsis"] !="": infoLabels['plot']= datos_tmdb["episodio_sinopsis"]
        if datos_tmdb["episodio_imagen"] !="": item.thumbnail= datos_tmdb["episodio_imagen"]
        #if datos_tmdb["episodio_titulo"] !="": title = title + " [COLOR 0xFFFFE6CC]" + datos_tmdb["episodio_titulo"].replace('\t','') + "[/COLOR]"
    except:
            pass
    
    def cap(l): 
        try:
            temporada_link = int(l["season"])
            capitulo_link = int(l['episode'])
        except:
            return False
        return True if temporada_link== int(infoLabels['season'])  and capitulo_link == int(infoLabels['episode']) else False    

    item.url= str(filter(cap, data_dict["link"])) #filtramos enlaces por capitulo

    item.infoLabels = infoLabels
    item.extra=str(data_dict['tmdb_id'])
    
    return findvideos(item)

def get_episodios(item):
    logger.info()
    itemlist = []
    plot={}
    
    try:
        from core.tmdb import Tmdb
        oTmdb= Tmdb(id_Tmdb= item.extra,tipo="tv")
    except:
        pass

    infoLabels = item.infoLabels

    lista_links=ast.literal_eval(item.url) 
    # Agrupar enlaces por episodios  temXcap
    temXcap_dict={}
    for link in lista_links:
        title_id = link['title_id']
        try:
            season = str(int(link['season']))
            episode = str(int(link['episode'])).zfill(2)
        except:
            continue
        id= season + "x" + episode
        if temXcap_dict.has_key(id):
            l= temXcap_dict[id]
            l.append(link)
            temXcap_dict[id]= l
        else:
            temXcap_dict[id]= [link]
            
    # Ordenar lista de enlaces por temporada y capitulo
    temXcap_list=temXcap_dict.items()
    temXcap_list.sort(key=lambda x: (int(x[0].split("x")[0]),int(x[0].split("x")[1])))
    for episodio in temXcap_list:
        title= infoLabels['titleraw'] + ' (' + episodio[0] + ')'
        infoLabels['season'], infoLabels['episode']=  episodio[0].split('x')
        try:
            # añadimos sinopsis e imagenes para cada capitulo
            datos_tmdb=oTmdb.get_episodio(temporada= infoLabels['season'],capitulo= infoLabels['episode'])
            if datos_tmdb["episodio_sinopsis"] !="": infoLabels['plot']= datos_tmdb["episodio_sinopsis"]
            if datos_tmdb["episodio_imagen"] !="": item.thumbnail= datos_tmdb["episodio_imagen"]
            if datos_tmdb["episodio_titulo"] !="": title = title + " " + datos_tmdb["episodio_titulo"].replace('\t','')
        except:
                pass

        itemlist.append( Item( channel=item.channel, action="findvideos", title=title, url=str(episodio[1]),
                               extra=item.extra, show=infoLabels['tvshowtitle'], fanart=item.fanart,
                               infoLabels = infoLabels,
                               thumbnail=item.thumbnail, viewmode="movie_with_plot", text_color="0xFFFFCE9C") )
    
    if config.get_library_support() and itemlist:
        url= urlparse.urljoin(__url_base__,"episodio-online/" + str(title_id))
        itemlist.append( Item(channel=item.channel, title="Añadir esta serie a la biblioteca", url=url,
                              text_color="0xFFe5ffcc", action="add_serie_to_library", extra='episodios###serie_add',
                              show= infoLabels['tvshowtitle'],
                              thumbnail = 'https://raw.githubusercontent.com/master-1970/resources/master/images/channels/pepecine/tv.png'))

    
    return itemlist
       
def findvideos(item):
    logger.info()
    itemlist = []
    #logger.debug(item)
    
    for link in ast.literal_eval(item.url):
        url= link["url"]
        flag= scrapertools.find_single_match(link["label"],'(\s*\<img src=.*\>)')
        idioma=link["label"].replace(flag,"")
        if link["quality"] !="?":
          calidad=(' [' +link["quality"]+ ']')
        else:
          calidad=""
        video= find_videos(link["url"])
    
        if video["servidor"]!="":
            servidor=video["servidor"]
            url=video["url"]
            title= "Ver en " + servidor.capitalize() + calidad + ' (' + idioma + ')'
            itemlist.append(item.clone(action="play", viewmode="list", server=servidor, title=title,
                                  text_color="0xFF994D00",url=url, folder=False) )
            
    return itemlist
    
def find_videos(url):
    #logger.info()
    ret = {'titulo':"",
           'url':"",
           'servidor':""}
    
    # Ejecuta el find_videos en cada servidor hasta que encuentra una coicidencia
    lista_servers = servertools.get_servers_list()
    for serverid in lista_servers:
        try:
            servers_module = __import__("servers."+serverid)
            server_module = getattr(servers_module,serverid)
            devuelve= server_module.find_videos(url)
            
            if devuelve:
                ret["titulo"]=devuelve[0][0]
                ret["url"]=devuelve[0][1]
                ret["servidor"]=devuelve[0][2]
                # reordenar el listado, es probable q el proximo enlace sea del mismo servidor
                lista_servers.remove(serverid)
                lista_servers.insert(0,serverid)
                break
           
        except ImportError:
            logger.info("No existe conector para #"+serverid+"#")
            #import traceback
            #logger.info(traceback.format_exc())
        except:
            logger.error("Error en el conector #"+serverid+"#")
            import traceback
            logger.info(traceback.format_exc())
    
    return ret
    
    pass
    
def episodios(item):
    # Necesario para las actualizaciones automaticas
    return get_temporadas(Item(channel=__chanel__ ,url=item.url, show=item.show, extra= "serie_add"))

