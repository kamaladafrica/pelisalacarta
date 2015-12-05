# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para bityouth
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os,sys

from core import logger
from core import config
from core import scrapertools
from core import jsontools
from core.item import Item
from servers import servertools
try:
    import xbmc
    import xbmcgui
except: pass
__channel__ = "bityouth"
__category__ = "F,S,A"
__type__ = "generic"
__title__ = "Bityouth"
__language__ = "ES"



DEBUG = config.get_setting("debug")
host="http://bityouth.com/"





def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.bityouth mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="[COLOR skyblue][B]Generos[/B][/COLOR]"      , action="generos", url="http://bityouth.com", thumbnail="http://s6.postimg.org/ybey4gxu9/bityougenerosthum3.png", fanart="http://s18.postimg.org/l4judlx09/bityougenerosfan.jpg"))
    itemlist.append( Item(channel=__channel__, title="[COLOR skyblue][B]Puntuacion[/B][/COLOR]"      , action="scraper", url="http://bityouth.com/more_elements/0/?o=pd", thumbnail="http://s6.postimg.org/n1qtn9i6p/bityoupuntothum4.png", fanart="http://s6.postimg.org/qrh9oof9t/bityoupuntofan.jpg"))
    itemlist.append( Item(channel=__channel__, title="[COLOR skyblue][B]Novedades[/B][/COLOR]" , action="scraper", url="http://bityouth.com/more_elements/0/?o=",  thumbnail="http://s6.postimg.org/bry3sbd5d/bityounovedathum2.png", fanart="http://s6.postimg.org/ys4r4naz5/bityounovedadfan.jpg"))
    import xbmc, time
    if xbmc.Player().isPlaying():
       xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    SEARCHDESTFILE= os.path.join(xbmc.translatePath('special://userdata/keymaps'), "search.txt")
    TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
    KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
    REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
    APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
    try:
        os.remove(KEYMAPDESTFILE)
        print "Custom Keyboard.xml borrado"
        os.remove(TESTPYDESTFILE)
        print "Testpy borrado"
        os.remove(REMOTEDESTFILE)
        print "Remote borrado"
        os.remove(APPCOMMANDDESTFILE)
        print "Appcommand borrado"
        xbmc.executebuiltin('Action(reloadkeymaps)')
    except Exception as inst:
        xbmc.executebuiltin('Action(reloadkeymaps)')
        print "No hay customs"
    itemlist.append( Item(channel=__channel__, title="[COLOR skyblue][B]Series[/B][/COLOR]" , action="scraper", url="http://bityouth.com/more_elements/0/genero/serie_de_tv?o=",  thumbnail="http://s6.postimg.org/59j1km53l/bityouseriesthum.png", fanart="http://s6.postimg.org/45yx8nkgh/bityouseriesfan3.jpg"))
    if xbmc.Player().isPlaying():
        xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
    KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
    REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
    APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
    TRAILERDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "trailer.txt")
    try:
        os.remove(KEYMAPDESTFILE)
        print "Custom Keyboard.xml borrado"
        os.remove(TESTPYDESTFILE)
        print "Testpy borrado"
        os.remove(REMOTEDESTFILE)
        print "Remote borrado"
        os.remove(APPCOMMANDDESTFILE)
        print "Appcommand borrado"
        xbmc.executebuiltin('Action(reloadkeymaps)')
    except Exception as inst:
        xbmc.executebuiltin('Action(reloadkeymaps)')
        print "No hay customs"
    try:
       os.remove(SEARCHDESTFILE)
       print "Custom search.txt borrado"
    except:
       print "No hay search.txt"

    try:
        os.remove(TRAILERDESTFILE)
        print "Custom Trailer.txt borrado"
    except:
        print "No hay Trailer.txt"
    itemlist.append( Item(channel=__channel__, title="[COLOR skyblue][B]Buscar...[/B][/COLOR]" , action="search", url="",  thumbnail="http://s6.postimg.org/48isvho41/bityousearchthum.png", fanart="http://s6.postimg.org/ic5hcegk1/bityousearchfan.jpg", plot = "search"))
    

    

    return itemlist


def search(item,texto):
    logger.info("pelisalacarta.bityouth search")
    itemlist = []
    
    
    if item.url=="":
        item.url="http://bityouth.com/busqueda/"

    item.url = item.url+texto
    item.url = item.url.replace("+","%20")

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    
    patron='<div class="title">.*?title="([^<]+)" '
    patron+= 'href="([^"]+)".*?'
    patron+='<h2 itemprop="name">([^<]+)</h2>.*?'
    patron+='<img itemprop="image" src="([^"]+)".*?'
    patron+='<a href="/year/(\d+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    if len(matches)==0 :
       itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]Sin resultados...[/B][/COLOR]", thumbnail ="http://s6.postimg.org/jp5jx97ip/bityoucancel.png", fanart ="http://s6.postimg.org/vfjhen0b5/bityounieve.jpg",folder=False) )
    
    for scrapedrate, scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear  in matches:
        if " /10" in scrapedrate:
            scrapedrate= scrapedrate.replace(" /10"," [COLOR red]Sin Puntuacion[/COLOR] ")
            scrapedrate= scrapedrate.replace("Valoracion","")
        trailer = scrapedtitle + " " + scrapedyear + " trailer"
        trailer = urllib.quote(trailer)
        scrapedtitle=scrapedtitle.replace(scrapedtitle,"[COLOR white]"+scrapedtitle+"[/COLOR]")
        scrapedrate=scrapedrate.replace(scrapedrate,"[COLOR gold][B]"+scrapedrate+"[/B][/COLOR]")
        scrapedrate= scrapedrate.replace("Valoracion","[COLOR skyblue]Valoracion[/COLOR]")
        scrapedtitle = scrapedtitle.replace("(Serie de TV)","")
        scrapedtitle = scrapedtitle.replace("torrent","")
        title = scrapedtitle + "--" + scrapedrate
        url = urlparse.urljoin(host,scrapedurl)
        thumbnail = urlparse.urljoin(host,scrapedthumbnail)
        if "_serie_de_tv" in scrapedurl:
           import xbmc
           SEARCHDESTFILE= os.path.join(xbmc.translatePath('special://userdata/keymaps'), "search.txt")
           urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/search.txt", SEARCHDESTFILE )
            
        itemlist.append( Item(channel=__channel__, action="fanart" , title=title , url=url, thumbnail=thumbnail, fanart="http://s6.postimg.org/y1uehu24x/bityougeneralfan.jpg",plot= trailer, folder=True))
        
    return itemlist
def generos(item):
    logger.info("pelisalacarta.bityouth search")
    itemlist = []
    
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    patron= '<li><a href="([^<]+)" title.*?Bityouth">([^<]+)</a></li>'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        if "Acción" in scrapedtitle:
            thumbnail= "http://s6.postimg.org/tbbxshsgh/bityouaccionthumb.png"
            fanart= "http://s6.postimg.org/iagsnh07l/bityouaccion.jpg"
        elif  "Animación" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/4w3prftjl/bityouanimacionthum.png"
               fanart= "http://s6.postimg.org/n06qc2r81/bityouanimacionfan.jpg"
        elif  "Aventuras" in scrapedtitle:
                thumbnail= "http://s6.postimg.org/bdr7ootap/bityouadventurethum.png"
                fanart= "http://s6.postimg.org/lzb30ozm9/bityouadventurefan.jpg"
        elif  "Bélica" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/5fdeegac1/bityouguerrathum.png"
               fanart= "http://s6.postimg.org/acqyzkcb5/bityouguerrafan.jpg"
        elif  "Ciencia" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/cxwjn31ox/bityoucienciaficcionthum.png"
               fanart= "http://s6.postimg.org/gszxpnkup/cienciaficcionbityoufan.jpg"
        elif  "Cine" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/y7orbo7dd/bityoucinenegrothum.png"
               fanart= "http://s6.postimg.org/m4jfo3wb5/bityoucinenegrofan.jpg"
        elif  "Comedia" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/jea3qwzm9/bityouxomediathum.png"
               fanart= "http://s6.postimg.org/v4o18asep/bityoucomediafan2.png"
        elif  "Docu" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/ifyc2dbo1/bityoudocuthumb.png"
               fanart= "http://s6.postimg.org/xn9q8ze4x/bityoudocufan.jpg"
        elif  "Drama" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/5r41ip5jl/bityoudramathumb.png "
               fanart= "http://s6.postimg.org/wawmku635/bityoudramafan.jpg"
        elif  "Fant" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/9sl4ocxu9/bityoufantasiathum.png"
               fanart= "http://s6.postimg.org/xiakd1w7l/bityoufantasiafan.jpg"
        elif  "Infantil" in scrapedtitle:
               thumbnail= "http://s6.postimg.org/j6e75o7rl/bityouinfathumb.png"
               fanart= "http://s6.postimg.org/f4s22w95d/bityouanimacionfan.jpg"
        elif  "Intriga" in scrapedtitle:
               thumbnail= "http://s22.postimg.org/vpmmbystd/bityouintrigthum.png"
               fanart= "http://s27.postimg.org/zee2hh7xv/bityouintrigfan.jpg"
        elif  "Musical" in scrapedtitle:
               thumbnail= "http://s8.postimg.org/u3wlw5eet/bityoumusithum.png"
               fanart= "http://s17.postimg.org/l21xuwt5r/bityoumusifan.jpg"
        elif  "Romance" in scrapedtitle:
               thumbnail= "http://s4.postimg.org/q6v7eq6e5/bityouromancethum.png"
               fanart= "http://s9.postimg.org/3o4qd4dsf/bityouromancefan.jpg"
        elif  "Terror" in scrapedtitle:
               thumbnail= "http://s9.postimg.org/yntipquvj/bityouterrorthum.png"
               fanart= "http://s3.postimg.org/wwq3dnpgz/bityouterrorfan.jpg"
        elif  "Thr" in scrapedtitle:
               thumbnail= "http://s17.postimg.org/eldin5an3/bityouthrithum.png"
               fanart= "http://s2.postimg.org/fnqykvb9l/bityouthrifan.jpg"
        elif  "West" in scrapedtitle:
               thumbnail= "http://s23.postimg.org/hjq6wjakb/bityouwesterthum.png"
               fanart= "http://s7.postimg.org/wzrh42ltn/bityouwesterfan.jpg"

        
        scrapedtitle=scrapedtitle.replace("ó","o")
        scrapedtitle=scrapedtitle.replace("é","e")
        url = "http://bityouth.com/more_elements/0/genero/"+scrapedtitle

        itemlist.append( Item(channel=__channel__, action="scraper" , title=scrapedtitle , thumbnail=thumbnail, fanart= fanart, url=url,  folder=True))

    return itemlist




def scraper(item):
    logger.info("pelisalacarta.bityouth search")
    itemlist = []
    import xbmc
    if xbmc.Player().isPlaying():
        xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    
    TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
    KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
    REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
    APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
    TRAILERDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "trailer.txt")
    try:
        os.remove(KEYMAPDESTFILE)
        print "Custom Keyboard.xml borrado"
        os.remove(TESTPYDESTFILE)
        print "Testpy borrado"
        os.remove(REMOTEDESTFILE)
        print "Remote borrado"
        os.remove(APPCOMMANDDESTFILE)
        print "App borrado"
        xbmc.executebuiltin('Action(reloadkeymaps)')
    except Exception as inst:
        xbmc.executebuiltin('Action(reloadkeymaps)')
        print "No hay customs"
    try:
        os.remove(TRAILERDESTFILE)
        print "Trailer.txt borrado"
    except:
        print "No hay Trailer.txt"

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|&amp;","",data)

    patron='<div class="title">.*?title="([^<]+)" '
    patron+= 'href="([^"]+)".*?'
    patron+='<h2 itemprop="name">([^<]+)</h2>.*?'
    patron+='<img itemprop="image" src="([^"]+)".*?'
    patron+='<a href="/year/(\d+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    
    for scrapedrate, scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear  in matches:
        if " /10" in scrapedrate:
            scrapedrate= scrapedrate.replace(" /10"," [COLOR red]Sin Puntuacion[/COLOR] ")
            scrapedrate= scrapedrate.replace("Valoracion","")
        trailer = scrapedtitle + " " + scrapedyear + " trailer"
        trailer = urllib.quote(trailer)
        scrapedtitle=scrapedtitle.replace(scrapedtitle,"[COLOR white]"+scrapedtitle+"[/COLOR]")
        scrapedrate=scrapedrate.replace(scrapedrate,"[COLOR gold][B]"+scrapedrate+"[/B][/COLOR]")
        scrapedrate= scrapedrate.replace("Valoracion","[COLOR skyblue]Valoracion[/COLOR]")
        scrapedtitle = scrapedtitle.replace("(Serie de TV)","")
        scrapedtitle = scrapedtitle.replace("torrent","")
        
        title = scrapedtitle + "--" + scrapedrate
        url = urlparse.urljoin(host,scrapedurl)
        thumbnail = urlparse.urljoin(host,scrapedthumbnail)
        
        
        itemlist.append( Item(channel=__channel__, action="fanart" , title=title , url=url, thumbnail=thumbnail, fanart="http://s6.postimg.org/y1uehu24x/bityougeneralfan.jpg", plot= trailer, folder=True))
    
    #paginacion
    data = scrapertools.cache_page(item.url)
    if not "<div class=\"title\">" in data:
           itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]No hay mas paginas...[/B][/COLOR]", thumbnail ="http://s6.postimg.org/f4es4kyfl/bityou_Sorry.png", fanart ="http://s6.postimg.org/y1uehu24x/bityougeneralfan.jpg",folder=False) )
    else:
    
         current_page_number = int(scrapertools.get_match(item.url,'more_elements/(\d+)'))
         item.url = re.sub(r"more_elements/\d+","more_elements/{0}",item.url)

         next_page_number = current_page_number + 40
         next_page = item.url.format(next_page_number)
    
         title= "[COLOR skyblue]Pagina siguiente>>[/COLOR]"
    
         itemlist.append( Item(channel=__channel__, title=title, url=next_page, fanart="http://s6.postimg.org/y1uehu24x/bityougeneralfan.jpg", thumbnail="http://s6.postimg.org/kbzv91f0x/bityouflecha2.png",
                              action="scraper", folder=True) )



    return itemlist

def fanart(item):
    
    
    #Vamos a sacar todos los fanarts y arts posibles
    logger.info("pelisalacarta.bityouth fanart")
    itemlist = []
    url = item.url
    data = scrapertools.cachePage(url)
    data = re.sub(r"\n|\r|\t|\s{2}|\(.*?\)|\[.*?\]|&nbsp;","",data)

    if not "_serie_de_tv" in item.url:
        title= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
        title = title.replace("(Serie de TV)","")
        title = title.replace("torrent","")
        title= title.replace(' ','%20')
        url="http://api.themoviedb.org/3/search/movie?api_key=57983e31fb435df4df77afb854740ea9&query=" + title + "&language=es&include_adult=false"
        data = scrapertools.cachePage(url)
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
        patron = '"page":1.*?,"id":(.*?),.*?"backdrop_path":"\\\(.*?)"'
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)==0:
            extra=item.thumbnail
            show= item.thumbnail
            posterdb = item.thumbnail
            fanart_info = item.thumbnail
            fanart_trailer = item.thumbnail
            category= item.thumbnail
            itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos_pelis", thumbnail=item.thumbnail, fanart=item.thumbnail ,extra=extra, show=show, category= category, folder=True) )
        else:
             for id, fan in matches:
                 try:
                     posterdb = scrapertools.get_match(data,'"page":1,.*?"poster_path":"\\\(.*?)"')
                     posterdb =  "https://image.tmdb.org/t/p/original" + posterdb
                 except:
                    posterdb = item.thumbnail
                 fanart="https://image.tmdb.org/t/p/original" + fan
                 item.extra= fanart
                 url ="http://api.themoviedb.org/3/movie/"+id+"/images?api_key=57983e31fb435df4df77afb854740ea9"
                 data = scrapertools.cachePage(url)
                 data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
                             
                 patron = '"backdrops".*?"file_path":".*?",.*?"file_path":"(.*?)",.*?"file_path":"(.*?)",.*?"file_path":"(.*?)"'
                 matches = re.compile(patron,re.DOTALL).findall(data)
                                     
                 if len(matches) == 0:
                     patron = '"backdrops".*?"file_path":"(.*?)",.*?"file_path":"(.*?)",.*?"file_path":"(.*?)"'
                     matches = re.compile(patron,re.DOTALL).findall(data)
                     if len(matches) == 0:
                        fanart_info = item.extra
                        fanart_trailer = item.extra
                        fanart_2 = item.extra
                 for fanart_info, fanart_trailer, fanart_2 in matches:
                     fanart_info = "https://image.tmdb.org/t/p/original" + fanart_info
                     fanart_trailer = "https://image.tmdb.org/t/p/original" + fanart_trailer
                     fanart_2 = "https://image.tmdb.org/t/p/original" + fanart_2

        #fanart_2 y arts

                 url ="http://webservice.fanart.tv/v3/movies/"+id+"?api_key=dffe90fba4d02c199ae7a9e71330c987"
                 data = scrapertools.cachePage(url)
                 data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
                 patron = '"hdmovielogo":.*?"url": "([^"]+)"'
                 matches = re.compile(patron,re.DOTALL).findall(data)
                 if '"moviedisc"' in data:
                     disc = scrapertools.get_match(data,'"moviedisc":.*?"url": "([^"]+)"')
                 if '"movieposter"' in data:
                      poster = scrapertools.get_match(data,'"movieposter":.*?"url": "([^"]+)"')
                 if '"moviethumb"' in data:
                     thumb = scrapertools.get_match(data,'"moviethumb":.*?"url": "([^"]+)"')
                 if '"moviebanner"' in data:
                     banner= scrapertools.get_match(data,'"moviebanner":.*?"url": "([^"]+)"')

                 if len(matches)==0:
                    extra=  item.thumbnail
                    show = fanart_2
                    category = item.extra
                    itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url, thumbnail=item.thumbnail, fanart=item.extra,  extra=extra, show=show, category= category, folder=True) )

             for logo in matches:
                 if '"hdmovieclearart"' in data:
                     clear=scrapertools.get_match(data,'"hdmovieclearart":.*?"url": "([^"]+)"')
                     if '"moviebackground"' in data:
                         extra=clear
                         show= fanart_2
                         if '"moviebanner"' in data:
                             category= banner
                         else:
                             category= clear
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url,  thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
                     else:
                          extra= clear
                          show=fanart_2
                          if '"moviebanner"' in data:
                              category = banner
                          else:
                               category = clear
                          itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url,  thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
                
                 if '"moviebackground"' in data:
                     
                     if '"hdmovieclearart"' in data:
                         clear=scrapertools.get_match(data,'"hdmovieclearart":.*?"url": "([^"]+)"')
                         extra=clear
                         show= fanart_2
                         if '"moviebanner"' in data:
                             category= banner
                         else:
                             category= clear
                    
                     else:
                         extra=logo
                         show= fanart_2
                         if '"moviebanner"' in data:
                             category= banner
                         else:
                             category= logo
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url,  thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category,  folder=True) )

                 if not '"hdmovieclearart"' in data and not '"moviebackground"' in data:
                        extra= logo
                        show=  fanart_2
                        if '"moviebanner"' in data:
                             category= banner
                        else:
                            category= item.extra
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url,  thumbnail=logo, fanart=item.extra,category= category, extra=extra,show=show ,  folder=True) )
    if "_serie_de_tv" in item.url:
        import xbmc
        SEARCHDESTFILE= os.path.join(xbmc.translatePath('special://userdata/keymaps'), "search.txt")
        TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
        KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
        REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
        APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
        TRAILERDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "trailer.txt")
        title= scrapertools.get_match(data,'<h1>Descarga <span itemprop="name">(.*?)<\/span>')
        title = title[title.find("(")+1:title.find(")")]
        title = title.replace("'","")
        title = title.replace("í","i")
        title= title.replace(' ','%20')
        title_tunes= title.replace('%20','+')
        import xbmc,time
        if not xbmc.Player().isPlaying() and not os.path.exists ( TRAILERDESTFILE ):
            
            TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
            KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
            REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
            APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
            try:
                os.remove(KEYMAPDESTFILE)
                print "Custom Keyboard.xml borrado"
                os.remove(TESTPYDESTFILE)
                print "Testpy borrado"
                os.remove(REMOTEDESTFILE)
                print "Remote borrado"
                os.remove(APPCOMMANDDESTFILE)
                print "Appcommand borrado"
                xbmc.executebuiltin('Action(reloadkeymaps)')
            except Exception as inst:
                xbmc.executebuiltin('Action(reloadkeymaps)')
                print "No hay customs"
                    
                try:
                   import  xbmc, time
                       
                   url ="http://www.televisiontunes.com/search.php?q=" + title_tunes
                   if "Anatomia+de+Grey" in url:
                      url="http://www.televisiontunes.com/search.php?q=greys+anatomy"
                   if "Big+Bang" in url:
                       url="http://www.televisiontunes.com/search.php?q=the+Big+Bang"
                   data = scrapertools.cachePage( url )
                   scrapedurl = scrapertools.get_match(data,'<div class=\'name\'>.*?<li><a href="(.*?)">')
                   url = "http://www.televisiontunes.com" + scrapedurl
                   if "Castle" in url :
                      url = "http://www.televisiontunes.com/Castle_-_Ending.html"
                   data = scrapertools.cachePage( url )
                   data = re.sub(r"\n|\r|\t|\s{2}|\(.*?\)|\[.*?\]|&nbsp;","",data)
                   song = scrapertools.get_match(data,'<form name="song_name_form">.*?type="hidden" value="(.*?)"')
                   song = song.replace (" ","%20")
                   xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
                   import xbmc, time
                   TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/test.py", TESTPYDESTFILE )
                   KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
                        
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/customkey.xml", KEYMAPDESTFILE )
                   REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/remote.xml", REMOTEDESTFILE )
                   APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/customapp.xml", APPCOMMANDDESTFILE )

                   xbmc.executebuiltin('Action(reloadkeymaps)')
                        
                except:
                    pass
        try:
           os.remove(TRAILERDESTFILE)
           print "Trailer.txt borrado"
           xbmc.executebuiltin('Action(reloadkeymaps)')
        except:
           print "No hay Trailer.txt"
           xbmc.executebuiltin('Action(reloadkeymaps)')
        if os.path.exists ( SEARCHDESTFILE ):
           
           try:
              os.remove(KEYMAPDESTFILE)
              print "Custom Keyboard.xml borrado"
              os.remove(TESTPYDESTFILE)
              print "Testpy borrado"
              os.remove(REMOTEDESTFILE)
              print "Remote borrado"
              os.remove(APPCOMMANDDESTFILE)
              print "Appcommand borrado"
              os.remove(SEARCHDESTFILE)
              print "search.txt borrado"
              xbmc.executebuiltin('Action(reloadkeymaps)')
           except Exception as inst:
              print "No hay customs"
              xbmc.executebuiltin('Action(reloadkeymaps)')
    
        url="http://thetvdb.com/api/GetSeries.php?seriesname=" + title + "&language=es"
        if "Érase%20una%20vez" in url:
            url ="http://thetvdb.com/api/GetSeries.php?seriesname=Erase%20una%20vez%20(2011)&language=es"
        if "Hawaii%20Five%200%20" in url:
            url ="http://thetvdb.com/api/GetSeries.php?seriesname=hawaii%205.0&language=es"
        if "The%20Big%20Bang%20Theory" in url:
            url = "http://thetvdb.com/api/GetSeries.php?seriesname=The%20Big%20Bang%20Theory%20%20&language=es"
        data = scrapertools.cachePage(url)
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
        patron = '<Data><Series><seriesid>([^<]+)</seriesid>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)==0:
            extra= item.thumbnail
            show=  item.thumbnail
            fanart_info = item.thumbnail
            fanart_trailer = item.thumbnail
            category= ""
            itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos", thumbnail=item.thumbnail, fanart=item.thumbnail ,extra=extra, category= category,  show=show , plot= item.plot, folder=True) )
        else:
        #fanart
            for id in matches:
                category = id
                id_serie = id
                url ="http://thetvdb.com/api/1D62F2F90030C444/series/"+id_serie+"/banners.xml"
                if "Castle" in title:
                    url ="http://thetvdb.com/api/1D62F2F90030C444/series/83462/banners.xml"
                data = scrapertools.cachePage(url)
                data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
                patron = '<Banners><Banner>.*?<VignettePath>(.*?)</VignettePath>'
                matches = re.compile(patron,re.DOTALL).findall(data)
                if len(matches)==0:
                    extra=item.thumbnail
                    show= item.thumbnail
                    fanart_info = item.thumbnail
                    fanart_trailer = item.thumbnail
                    itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos", thumbnail=item.thumbnail, fanart=item.thumbnail ,category = category, extra=extra, show=show,plot= item.plot, folder=True) )
                        
            for fan in matches:
                fanart="http://thetvdb.com/banners/" + fan
                item.extra= fanart
                patron= '<Banners><Banner>.*?<BannerPath>.*?</BannerPath>.*?</Banner><Banner>.*?<BannerPath>(.*?)</BannerPath>.*?</Banner><Banner>.*?<BannerPath>(.*?)</BannerPath>.*?</Banner><Banner>.*?<BannerPath>(.*?)</BannerPath>'
                matches = re.compile(patron,re.DOTALL).findall(data)
                if len(matches)==0:
                    fanart_info= item.extra
                    fanart_trailer = item.extra
                    fanart_2 = item.extra
                for fanart_info, fanart_trailer, fanart_2 in matches:
                    fanart_info = "http://thetvdb.com/banners/" + fanart_info
                    fanart_trailer = "http://thetvdb.com/banners/" + fanart_trailer
                    fanart_2 = "http://thetvdb.com/banners/" + fanart_2
            #clearart, fanart_2 y logo
            for id in matches:
                url ="http://webservice.fanart.tv/v3/tv/"+id_serie+"?api_key=dffe90fba4d02c199ae7a9e71330c987"
                if "Castle" in title:
                    url ="http://assets.fanart.tv/v3/tv/83462?api_key=dffe90fba4d02c199ae7a9e71330c987"
                data = scrapertools.cachePage(url)
                data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
                patron = '"clearlogo":.*?"url": "([^"]+)"'
                matches = re.compile(patron,re.DOTALL).findall(data)
                if '"tvposter"' in data:
                    tvposter = scrapertools.get_match(data,'"tvposter":.*?"url": "([^"]+)"')
                if '"tvbanner"' in data:
                    tvbanner = scrapertools.get_match(data,'"tvbanner":.*?"url": "([^"]+)"')
                if '"tvthumb"' in data:
                    tvthumb = scrapertools.get_match(data,'"tvthumb":.*?"url": "([^"]+)"')
                if '"hdtvlogo"' in data:
                    hdtvlogo = scrapertools.get_match(data,'"hdtvlogo":.*?"url": "([^"]+)"')
                if '"hdclearart"' in data:
                    hdtvclear = scrapertools.get_match(data,'"hdclearart":.*?"url": "([^"]+)"')
                if len(matches)==0:
                    if '"hdtvlogo"' in data:
                        if "showbackground" in data:
                            
                            if '"hdclearart"' in data:
                                 thumbnail = hdtvlogo
                                 extra=  hdtvclear
                                 show = fanart_2
                            else:
                                thumbnail = hdtvlogo
                                extra= thumbnail
                                show = fanart_2
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, category=category, extra=extra, show=show,plot= item.plot, folder=True) )
                        
                        
                        else:
                            if '"hdclearart"' in data:
                                thumbnail= hdtvlogo
                                extra= hdtvclear
                                show= fanart_2
                            else:
                                thumbnail= hdtvlogo
                                extra= thumbnail
                                show= fanart_2
                            
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra, show=show,  category= category,plot= item.plot, folder=True) )
                    else:
                         extra=  item.thumbnail
                         show = fanart_2
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=item.thumbnail, fanart=item.extra, extra=extra, show=show, category = category, plot= item.plot, folder=True) )
            for logo in matches:
                if '"hdtvlogo"' in data:
                    thumbnail = hdtvlogo
                elif not '"hdtvlogo"' in data :
                           if '"clearlogo"' in data:
                               thumbnail= logo
                else:
                    thumbnail= item.thumbnail
                if '"clearart"' in data:
                    clear=scrapertools.get_match(data,'"clearart":.*?"url": "([^"]+)"')
                    if "showbackground" in data:
                        
                        extra=clear
                        show= fanart_2
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show, category= category, plot= item.plot, folder=True) )
                    else:
                        extra= clear
                        show= fanart_2
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show, category= category, plot= item.plot, folder=True) )
        
                if "showbackground" in data:
                    
                    if '"clearart"' in data:
                         clear=scrapertools.get_match(data,'"clearart":.*?"url": "([^"]+)"')
                         extra=clear
                         show= fanart_2
                    else:
                         extra=logo
                         show= fanart_2
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show,  category = category, plot= item.plot, folder=True) )
                
                if not '"clearart"' in data and not '"showbackground"' in data:
                        if '"hdclearart"' in data:
                            extra= hdtvclear
                            show= fanart_2
                        else:
                             extra= thumbnail
                             show=  fanart_2
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show , category = category, plot= item.plot, folder=True) )


    title ="Info"
    if not "_serie_de_tv" in item.url:
        thumbnail = posterdb
    if "_serie_de_tv" in item.url:
        if '"tvposter"' in data:
            thumbnail= tvposter
        else:
            thumbnail = item.thumbnail

        if "tvbanner" in data:
            category = tvbanner
        else:
            category = show

    title = title.replace(title,"[COLOR cyan]"+title+"[/COLOR]")
    itemlist.append( Item(channel=__channel__, action="info" , title=title , url=item.url, thumbnail=thumbnail, fanart= fanart_info, extra = extra, show = show,folder=False ))
    ###trailer
   
   
    title= "[COLOR gold]Trailer[/COLOR]"
    if len(item.extra)==0:
        fanart=item.thumbnail
    else:
        fanart = item.extra
    if "_serie_de_tv" in item.url:
        if '"tvthumb"' in data:
            thumbnail = tvthumb
        else:
            thumbnail = item.thumbnail
        if '"tvbanner"' in data:
           extra= tvbanner
        elif '"tvthumb"' in data:
            extra = tvthumb
        else:
            extra = item.thumbnail
    else:
        if '"moviethumb"' in data:
            thumbnail = thumb
        else:
            thumbnail = posterdb

        if '"moviedisc"' in data:
            extra= disc
        else:
            if '"moviethumb"' in data:
                extra = thumb
        
            else:
                extra = posterdb


    itemlist.append( Item(channel=__channel__, action="trailer", title=title , url=item.url , thumbnail=thumbnail , plot=item.plot , fanart=fanart_trailer, extra=extra, folder=True) )

    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.bityouth search")
    itemlist = []
    import xbmc, time
    SEARCHDESTFILE= os.path.join(xbmc.translatePath('special://userdata/keymaps'), "search.txt")
    TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
    KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
    REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
    APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
    if  xbmc.Player().isPlaying():
        if not os.path.exists ( TESTPYDESTFILE ):
           import xbmc
           urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/search.txt", SEARCHDESTFILE )
           urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/test.py", TESTPYDESTFILE )
           urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/customkey.xml", KEYMAPDESTFILE )
           urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/remote.xml", REMOTEDESTFILE )
           urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/customapp.xml", APPCOMMANDDESTFILE )
                                                    
           xbmc.executebuiltin('Action(reloadkeymaps)')
   
    if not xbmc.Player().isPlaying():
        TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
        KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
        REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
        APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
        try:
            os.remove(KEYMAPDESTFILE)
            print "Custom Keyboard.xml borrado"
            os.remove(TESTPYDESTFILE)
            print "Testpy borrado"
            os.remove(REMOTEDESTFILE)
            print "Remote borrado"
            os.remove(APPCOMMANDDESTFILE)
            print "Appcommand borrado"
            xbmc.executebuiltin('Action(reloadkeymaps)')
        except Exception as inst:
            xbmc.executebuiltin('Action(reloadkeymaps)')
            print "No hay customs"

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    patron='<td><div style="width:125px.*?<td><small>([^<]+)</small>.*?'
    patron+='<td><small>([^<]+)</small>.*?'
    patron+='href="([^"]+)"'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    if len(matches)==0 :
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]Lo sentimos el torrent aún no está disponible...[/B][/COLOR]", thumbnail ="http://s6.postimg.org/f4es4kyfl/bityou_Sorry.png", fanart ="http://s6.postimg.org/guxt62fyp/bityounovideo.jpg",folder=False) )

    for scrapedcalidad, scrapedsize, scrapedurl in matches:
        
        scrapedurl = urlparse.urljoin(host,scrapedurl)
        season = scrapedcalidad
        season = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|V.O.S|Cast|Temp.|Cap.\d+| ","",season)
        epi=scrapedcalidad
        epi= re.sub(r"\n|\r|\t|\s{2}|V.O.S|Cast|&nbsp;|Temp.\d+|Cap.| ","",epi)
        title= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
        title = title.replace("(Serie de TV)","")
        title = title.replace("torrent","")
        title_info= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
        title_info = title_info.replace("(Serie de TV)","")
        title_info = title_info.replace("torrent","")
        title_info = title_info.replace(" ","%20")
        scrapedcalidad = scrapedcalidad.replace(scrapedcalidad,"[COLOR skyblue][B]"+scrapedcalidad+"[/B][/COLOR]")
        scrapedsize=scrapedsize.replace(scrapedsize,"[COLOR gold][B]"+scrapedsize+"[/B][/COLOR]")
        title=title.replace(title,"[COLOR white][B]"+title+"[/B][/COLOR]")+"-("+scrapedcalidad+"/"+scrapedsize+")"
        
        
        extra = season+"|"+title_info+"|"+epi
        itemlist.append( Item(channel=__channel__, title = title, action="episodios", url=scrapedurl, thumbnail=item.extra, fanart=item.show, extra=extra, category= item.category, folder=True) )





    return itemlist


def episodios(item):
    logger.info("pelisalacarta.bityouth episodios")
    itemlist = []
    import xbmc, time
    if not xbmc.Player().isPlaying():
        TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
        KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
        REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
        APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
        try:
            os.remove(KEYMAPDESTFILE)
            print "Custom Keyboard.xml borrado"
            os.remove(TESTPYDESTFILE)
            print "Testpy borrado"
            os.remove(REMOTEDESTFILE)
            print "Remote borrado"
            os.remove(APPCOMMANDDESTFILE)
            print "Appcommand borrado"
            xbmc.executebuiltin('Action(reloadkeymaps)')
        except Exception as inst:
            xbmc.executebuiltin('Action(reloadkeymaps)')
            print "No hay customs"

    season = item.extra.split("|")[0]
    title = item.extra.split("|")[1]
    epi = item.extra.split("|")[2]
    title_tag="[COLOR yellow]Ver --[/COLOR]"
    title = title_tag + item.title
    url="http://api.themoviedb.org/3/search/tv?api_key=57983e31fb435df4df77afb854740ea9&query="+ item.extra.split("|")[1] +"&language=es&include_adult=false"
    if "%2090210%20Sensacion%20de%20vivir" in url:
        url="http://api.themoviedb.org/3/search/tv?api_key=57983e31fb435df4df77afb854740ea9&query=90210&language=es&include_adult=false"
    if "%20De%20vuelta%20al%20nido%20" in url:
        url ="http://api.themoviedb.org/3/search/tv?api_key=57983e31fb435df4df77afb854740ea9&query=packed%20to%20the%20rafter&language=es&include_adult=false"
    if "%20Asuntos%20de%20estado%20" in url:
        url="http://api.themoviedb.org/3/search/tv?api_key=57983e31fb435df4df77afb854740ea9&query=state%20of%20affair&language=es&include_adult=false"
    if "%20Como%20defender%20a%20un%20asesino%20" in url:
        url="http://api.themoviedb.org/3/search/tv?api_key=57983e31fb435df4df77afb854740ea9&query=how%20to%20get%20away%20with%20murder&language=es&include_adult=false"
    data = scrapertools.cachePage(url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = '{"page".*?"backdrop_path":.*?,"id":(.*?),"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)==0:
        thumbnail= item.thumbnail
        fanart = item.fanart
        id = ""
        itemlist.append( Item(channel=__channel__, title = title , action="play", url=item.url, server="torrent", thumbnail=thumbnail, fanart=fanart,  folder=False) )
    for id in matches:
        if not '{"page":1,"results":[{"backdrop_path":null' in data:
                backdrop=scrapertools.get_match(data,'{"page".*?"backdrop_path":"(.*?)",.*?"id"')
                fanart_3 = "https://image.tmdb.org/t/p/original" + backdrop
                fanart = fanart_3
        else:
            fanart= item.fanart
        url ="https://api.themoviedb.org/3/tv/"+id+"/season/"+item.extra.split("|")[0]+"/episode/"+item.extra.split("|")[2]+"/images?api_key=57983e31fb435df4df77afb854740ea9"
        data = scrapertools.cachePage(url)
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
        patron = '{"id".*?"file_path":"(.*?)","height"'
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)==0:
            thumbnail = item.thumbnail
            itemlist.append( Item(channel=__channel__, title = title , action="play", url=item.url, server="torrent", thumbnail=thumbnail, fanart=fanart,  folder=False) )
        for foto in matches:
            thumbnail = "https://image.tmdb.org/t/p/original" + foto
            
            
            itemlist.append( Item(channel=__channel__, title = title , action="play", url=item.url, server="torrent", thumbnail=thumbnail, fanart=fanart,  category = item.category, folder=False) )
    ###thumb temporada###
    url= "http://api.themoviedb.org/3/tv/"+id+"/season/"+season+"/images?api_key=57983e31fb435df4df77afb854740ea9"
    data = scrapertools.cachePage( url )
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = '{"id".*?"file_path":"(.*?)","height"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches) == 0:
        thumbnail= item.thumbnail
    for temp in matches:
        thumbnail= "https://image.tmdb.org/t/p/original"+ temp
    ####fanart info####
    url ="http://api.themoviedb.org/3/tv/"+id+"/images?api_key=57983e31fb435df4df77afb854740ea9"
    data = scrapertools.cachePage( url )
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = '{"backdrops".*?"file_path":".*?","height".*?"file_path":"(.*?)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches) == 0:
        fanart = item.fanart
    for fanart_4 in matches:
        fanart = "https://image.tmdb.org/t/p/original" + fanart_4

    show = item.category+"|"+item.thumbnail
    print "@@@@"+show
    title ="Info"
    title = title.replace(title,"[COLOR skyblue]"+title+"[/COLOR]")
    itemlist.append( Item(channel=__channel__, action="info_capitulos" , title=title , url=item.url, thumbnail=thumbnail, fanart=fanart, extra = item.extra, show = show, folder=False ))

    return itemlist
def play(item):
    logger.info("pelisalacarta.bityouth play")
    itemlist = []
    if "youtube" in item.url:
        itemlist.append( Item(channel=__channel__, action="play", server="youtube",  url=item.url ,  fulltitle = item.title , fanart="http://s23.postimg.org/84vkeq863/movietrailers.jpg", folder=False) )
    
    
    itemlist.append( Item(channel=__channel__, title = item.title , action="play", url=item.url, server="torrent", thumbnail=item.thumbnail, fanart=item.fanart,  category = item.category, folder=False) )

    return itemlist

def findvideos_pelis(item):
    logger.info("pelisalacarta.bityouth findvideos_pelis")
    itemlist = []
    
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    patron='<td><div style="width:125px.*?<td><small>([^<]+)</small>.*?'
    patron+='<td><small>([^<]+)</small>.*?'
    patron+='href="([^"]+)"'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    if len(matches)==0 :
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]Lo sentimos el torrent aún no está disponible...[/B][/COLOR]", thumbnail ="http://s6.postimg.org/f4es4kyfl/bityou_Sorry.png", fanart ="http://s6.postimg.org/guxt62fyp/bityounovideo.jpg",folder=False) )

    for scrapedcalidad, scrapedsize, scrapedurl in matches:
        
        scrapedurl = urlparse.urljoin(host,scrapedurl)
        
        title= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
        title = title.replace("(Serie de TV)","")
        title = title.replace("torrent","")
        title_info= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
        title_info = title_info.replace("(Serie de TV)","")
        title_info = title_info.replace("torrent","")
        scrapedcalidad = scrapedcalidad.replace(scrapedcalidad,"[COLOR skyblue][B]"+scrapedcalidad+"[/B][/COLOR]")
        scrapedsize=scrapedsize.replace(scrapedsize,"[COLOR gold][B]"+scrapedsize+"[/B][/COLOR]")
        title=title.replace(title,"[COLOR white][B]"+title+"[/B][/COLOR]")+"-("+scrapedcalidad+"/"+scrapedsize+")"
        
            
        itemlist.append( Item(channel=__channel__, title=title, url=scrapedurl, fanart=item.show, thumbnail=item.extra, action="play", folder=False) )




    return itemlist

def trailer(item):
    logger.info("pelisalacarta.bityouth trailer")
    itemlist = []
    import xbmc
    TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
    if os.path.exists ( TESTPYDESTFILE ):
        TRAILERDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "trailer.txt")
        urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/trailer.txt", TRAILERDESTFILE )
    youtube_trailer = "https://www.youtube.com/results?search_query=" + item.plot + "español"
    
    data = scrapertools.cache_page(youtube_trailer)
    
    patron = '<a href="/watch?(.*?)".*?'
    patron += 'title="([^"]+)"'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    if len(matches)==0 :
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]No hay Trailer[/B][/COLOR]", thumbnail ="http://s6.postimg.org/jp5jx97ip/bityoucancel.png", fanart ="http://s6.postimg.org/vfjhen0b5/bityounieve.jpg",folder=False) )
    
    for scrapedurl, scrapedtitle in matches:
        
        scrapedurl = "https://www.youtube.com/watch"+scrapedurl
        scrapedtitle = scrapertools.decodeHtmlentities( scrapedtitle )
        scrapedtitle=scrapedtitle.replace(scrapedtitle,"[COLOR khaki][B]"+scrapedtitle+"[/B][/COLOR]")
        itemlist.append( Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, server="youtube", fanart="http://s6.postimg.org/g4gxuw91r/bityoutrailerfn.jpg", thumbnail=item.extra, action="play", folder=False) )

    return itemlist

def play(item):
    logger.info("pelisalacarta.bityouth play")
    itemlist = []
    
    if item.server == "youtube":
        itemlist.append( Item(channel=__channel__, title=item.plot, url=item.url, server="youtube", fanart=item.fanart, thumbnail=item.thumbnail, action="play", folder=False) )
    
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    patron = '<td><a class="btn btn-success" href="([^"]+)"'
    
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    for scrapedurl in matches:
        
       
        itemlist.append( Item(channel=__channel__, title=item.title, server="torrent", url=scrapedurl, fanart="http://s9.postimg.org/lmwhrdl7z/aquitfanart.jpg", thumbnail=item.thumbnail, action="play", folder=True) )
    
    
    
    return itemlist

def info(item):
    logger.info("pelisalacarta.sinluces trailer")
    url=item.url
    if "_serie_de_tv" in item.url:
        import xbmc
        APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
        try:
            os.remove(APPCOMMANDDESTFILE)
        except:
            pass
    
    data = scrapertools.cachePage(url)
    data = re.sub(r"\n|\r|\t|\s{2}|Descarga el torrent.*?en Bityouth.","",data)
    title= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
    title = title.upper()
    title = title.replace(title,"[COLOR gold][B]"+title+"[/B][/COLOR]")
    title = title.replace("TORRENT","")
    try:
       plot = scrapertools.get_match(data,'<div itemprop="description">(.*?)</div>')
       plot = plot.replace(plot,"[COLOR bisque][B]"+plot+"[/B][/COLOR]")
       plot = plot.replace("</i>","")
       plot = plot.replace("</br>","")
       plot = plot.replace("<br/>","")
       plot = plot.replace("&#8220","")
       plot = plot.replace("<b>","")
       plot = plot.replace("</b>","")
       plot = plot.replace(" &#8203;&#8203;","")
       plot= scrapertools.decodeHtmlentities( plot )
       plot = plot.replace("&quot;","")
    except:
        title = "[COLOR red][B]LO SENTIMOS...[/B][/COLOR]"
        plot = "Esta serie no tiene informacion..."
        plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
        photo="http://s6.postimg.org/nm3gk1xox/noinfosup2.png"
        foto ="http://s6.postimg.org/ub7pb76c1/noinfo.png"
        info =""
        quit = "Pulsa"+" [COLOR blue][B]INTRO [/B][/COLOR]"+ "para quitar"
    try:
       scrapedinfo = scrapertools.get_match(data,'<div class="col-sm-5 col-md-5 col-lg-4">(.*?)Título Original:')
       infoformat = re.compile('(.*?:).*?</strong>(.*?)<strong>',re.DOTALL).findall(scrapedinfo)
       for info ,info2 in infoformat:
           scrapedinfo= scrapedinfo.replace(info2,"[COLOR bisque]"+info2+"[/COLOR]")
           scrapedinfo= scrapedinfo.replace(info,"[COLOR aqua][B]"+info+"[/B][/COLOR]")
       info = scrapedinfo
       info = re.sub(r'<p class=".*?">|<strong>|</strong>|<a href="/year/.*?">| title=".*?"|alt=".*?"|>#2015|</a>|<span itemprop=".*?".*?>|<a.*?itemprop=".*?".*?">|</span>|<a href="/genero/.*?"|<a href=".*?"|itemprop="url">|"|</div><div class="col-sm-7 col-md-7 col-lg-8">|>,','',info)
       info = info.replace("</p>"," ")
       info = info.replace("#",",")
       info = info.replace(">","")
    except:
       info = "[COLOR skyblue][B]Sin informacion adicional...[/B][/COLOR]"
    foto = item.show
    photo= item.extra
    quit = "Pulsa"+" [COLOR blue][B]INTRO [/B][/COLOR]"+ "para quitar"
    if "_serie_de_tv" in item.url:

        NOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "noback.xml")
        REMOTENOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remotenoback.xml")
        APPNOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "appnoback.xml")
        urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/noback.xml", NOBACKDESTFILE )
        urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/remotenoback.xml", REMOTENOBACKDESTFILE)
        urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/appnoback.xml", APPNOBACKDESTFILE )
        xbmc.executebuiltin('Action(reloadkeymaps)')
    
    ventana2 = TextBox1(title=title, plot=plot, info=info, thumbnail=photo, fanart=foto, quit= quit)
    ventana2.doModal()
ACTION_SELECT_ITEM = 7
class TextBox1( xbmcgui.WindowDialog ):
         """ Create a skinned textbox window """
         def __init__( self, *args, **kwargs):
            
            self.getTitle = kwargs.get('title')
            self.getPlot = kwargs.get('plot')
            self.getInfo = kwargs.get('info')
            self.getThumbnail = kwargs.get('thumbnail')
            self.getFanart = kwargs.get('fanart')
            self.getQuit = kwargs.get('quit')
                            
            self.background = xbmcgui.ControlImage( 70, 20, 1150, 630, 'http://s6.postimg.org/58jknrvtd/backgroundventana5.png')
            self.title = xbmcgui.ControlTextBox(140, 60, 1130, 50)
            self.quit = xbmcgui.ControlTextBox(145, 90, 1030, 45)
            self.plot = xbmcgui.ControlTextBox( 120, 150, 1056, 140 )
            self.info = xbmcgui.ControlFadeLabel(120, 310, 1056, 100)
            self.thumbnail = xbmcgui.ControlImage( 813, 43, 390, 100, self.getThumbnail )
            self.fanart = xbmcgui.ControlImage( 120, 365, 1060, 250, self.getFanart )
                                                
            self.addControl(self.background)
            self.addControl(self.title)
            self.addControl(self.quit)
            self.addControl(self.plot)
            self.addControl(self.thumbnail)
            self.addControl(self.fanart)
            self.addControl(self.info)
                
            self.title.setText( self.getTitle )
            self.quit.setText( self.getQuit )
            try:
                self.plot.autoScroll(7000,6000,30000)
            except:
                print "Actualice a la ultima version de kodi para mejor info"
                import xbmc
                xbmc.executebuiltin('Notification([COLOR red][B]Actualiza Kodi a su última versión[/B][/COLOR], [COLOR skyblue]para mejor info[/COLOR],8000,"https://raw.githubusercontent.com/linuxserver/docker-templates/master/linuxserver.io/img/kodi-icon.png")')
            self.plot.setText(  self.getPlot )
            self.info.addLabel(self.getInfo)
                
         def get(self):
             self.show()
                
         def onAction(self, action):
             if action == ACTION_SELECT_ITEM:
                import os, sys
                import xbmc
                APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
                NOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "noback.xml")
                REMOTENOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remotenoback.xml")
                APPNOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "appnoback.xml")
                TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
                try:
                    os.remove(NOBACKDESTFILE)
                    os.remove(REMOTENOBACKDESTFILE)
                    os.remove(APPNOBACKDESTFILE)
                    if os.path.exists ( TESTPYDESTFILE ):
                        urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/customapp.xml", APPCOMMANDDESTFILE )
                    xbmc.executebuiltin('Action(reloadkeymaps)')
                except:
                    xbmc.executebuiltin('Action(reloadkeymaps)')
                self.close()

def test():
    return True

def info_capitulos(item):
    logger.info("pelisalacarta.Bityouth info_capitulos")
    import xbmc
    APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
    try:
        os.remove(APPCOMMANDDESTFILE)
    except:
        pass
    item.category = item.show.split("|")[0]
    item.thumbnail = item.show.split("|")[1]
    
    url="http://thetvdb.com/api/1D62F2F90030C444/series/"+item.show.split("|")[0]+"/default/"+item.extra.split("|")[0]+"/"+item.extra.split("|")[2]+"/es.xml"
    data = scrapertools.cache_page(url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = '<Data>.*?<EpisodeName>([^<]+)</EpisodeName>.*?'
    patron += '<Overview>(.*?)</Overview>.*?'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)==0 :
        title = "[COLOR red][B]LO SENTIMOS...[/B][/COLOR]"
        plot = "Este capitulo no tiene informacion..."
        plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
        foto = "http://s6.postimg.org/nm3gk1xox/noinfosup2.png"
        image="http://s6.postimg.org/ub7pb76c1/noinfo.png"
        quit = "Pulsa"+" [COLOR greenyellow][B]INTRO [/B][/COLOR]"+ "para quitar"

    else :
    
    
         for name_epi, info in matches:
             if "<filename>episodes" in data:
                foto = scrapertools.get_match(data,'<Data>.*?<filename>(.*?)</filename>')
                fanart = "http://thetvdb.com/banners/" + foto
             else:
                fanart=item.show.split("|")[1]
                
             plot = info
             plot = plot.replace(plot,"[COLOR burlywood][B]"+plot+"[/B][/COLOR]")
             title = name_epi.upper()
             title = title.replace(title,"[COLOR skyblue][B]"+title+"[/B][/COLOR]")
             image=fanart
             foto= item.show.split("|")[1]
             quit = "Pulsa"+" [COLOR greenyellow][B]INTRO [/B][/COLOR]"+ "para quitar"
             NOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "noback.xml")
             REMOTENOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remotenoback.xml")
             APPNOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "appnoback.xml")
             TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
             urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/noback.xml", NOBACKDESTFILE )
             urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/remotenoback.xml", REMOTENOBACKDESTFILE)
             urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/appnoback.xml", APPNOBACKDESTFILE )
             xbmc.executebuiltin('Action(reloadkeymaps)')
    ventana = TextBox2(title=title, plot=plot, thumbnail=image, fanart=foto, quit= quit)
    ventana.doModal()



ACTION_SELECT_ITEM = 7
class TextBox2( xbmcgui.WindowDialog ):
        """ Create a skinned textbox window """
        def __init__( self, *args, **kwargs):
            self.getTitle = kwargs.get('title')
            self.getPlot = kwargs.get('plot')
            self.getThumbnail = kwargs.get('thumbnail')
            self.getFanart = kwargs.get('fanart')
            self.getQuit = kwargs.get('quit')
            
            self.background = xbmcgui.ControlImage( 70, 20, 1150, 630, 'http://s6.postimg.org/n3ph1uxn5/ventana.png')
            self.title = xbmcgui.ControlTextBox(120, 60, 430, 50)
            self.quit = xbmcgui.ControlTextBox(145, 90, 1030, 45)
            self.plot = xbmcgui.ControlTextBox( 120, 150, 1056, 100 )
            self.thumbnail = xbmcgui.ControlImage( 120, 300, 1056, 300, self.getThumbnail )
            self.fanart = xbmcgui.ControlImage( 780, 43, 390, 100, self.getFanart )
            
            self.addControl(self.background)
            self.addControl(self.title)
            self.addControl(self.quit)
            self.addControl(self.plot)
            self.addControl(self.thumbnail)
            self.addControl(self.fanart)
            
            self.title.setText( self.getTitle )
            self.quit.setText( self.getQuit )
            try:
                self.plot.autoScroll(7000,6000,30000)
            except:
                print "Actualice a la ultima version de kodi para mejor info"
                import xbmc
                xbmc.executebuiltin('Notification([COLOR red][B]Actualiza Kodi a su última versión[/B][/COLOR], [COLOR skyblue]para mejor info[/COLOR],8000,"https://raw.githubusercontent.com/linuxserver/docker-templates/master/linuxserver.io/img/kodi-icon.png")')
            self.plot.setText(  self.getPlot )
        
        def get(self):
            self.show()
        
        def onAction(self, action):
            if action == ACTION_SELECT_ITEM:
               import os, sys
               import xbmc
               APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
               NOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "noback.xml")
               REMOTENOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remotenoback.xml")
               APPNOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "appnoback.xml")
               TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
               try:
                  os.remove(NOBACKDESTFILE)
                  os.remove(REMOTENOBACKDESTFILE)
                  os.remove(APPNOBACKDESTFILE)
                  if os.path.exists ( TESTPYDESTFILE ):
                     urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bityouth/customapp.xml", APPCOMMANDDESTFILE )
                  xbmc.executebuiltin('Action(reloadkeymaps)')
               except:
                  xbmc.executebuiltin('Action(reloadkeymaps)')
               self.close()
def test():
    return True





