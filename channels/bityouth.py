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
    itemlist.append( Item(channel=__channel__, title="[COLOR skyblue][B]Series[/B][/COLOR]" , action="scraper", url="http://bityouth.com/more_elements/0/genero/serie_de_tv?o=",  thumbnail="http://s6.postimg.org/59j1km53l/bityouseriesthum.png", fanart="http://s6.postimg.org/45yx8nkgh/bityouseriesfan3.jpg"))
    itemlist.append( Item(channel=__channel__, title="[COLOR skyblue][B]Buscar...[/B][/COLOR]" , action="search", url="",  thumbnail="http://s6.postimg.org/48isvho41/bityousearchthum.png", fanart="http://s6.postimg.org/ic5hcegk1/bityousearchfan.jpg"))
    

    

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
           scrapedrate= scrapedrate.replace(" /10"," [COLOR red][B]Sin Puntuacion[/B][/COLOR] ")
        trailer = scrapedtitle + " " + scrapedyear + " trailer"
        trailer = urllib.quote(trailer)
        title = scrapedtitle + "--" + scrapedrate
        url = urlparse.urljoin(host,scrapedurl)
        thumbnail = urlparse.urljoin(host,scrapedthumbnail)
        
            
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
        patron = '"page":1.*?"backdrop_path":"(.*?)".*?,"id":(.*?),'
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)==0:
            extra=item.thumbnail
            show= item.thumbnail
            category= item.thumbnail
            itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos_pelis", thumbnail=item.thumbnail, fanart=item.thumbnail ,extra=extra, show=show, category= category, folder=True) )
        else:
             for fan, id in matches:
                 fanart="https://image.tmdb.org/t/p/original" + fan
                 item.extra= fanart

        #fanart_2 y arts

                 url ="http://assets.fanart.tv/v3/movies/"+id+"?api_key=6fa42b0ef3b5f3aab6a7edaa78675ac2"
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
                    show = item.extra
                    category = item.extra
                    itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url, thumbnail=item.thumbnail, fanart=item.extra,  extra=extra, show=show, category= category, folder=True) )

             for logo in matches:
                 if '"hdmovieclearart"' in data:
                     clear=scrapertools.get_match(data,'"hdmovieclearart":.*?"url": "([^"]+)"')
                     if '"moviebackground"' in data:
                         fanart_2=scrapertools.get_match(data,'"moviebackground":.*?"url": "([^"]+)"')
                         extra=clear
                         show= fanart_2
                         if '"moviebanner"' in data:
                             category= banner
                         else:
                             category= clear
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url,  thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
                     else:
                          extra= clear
                          show=item.extra
                          if '"moviebanner"' in data:
                              category = banner
                          else:
                               category = clear
                          itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url,  thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
                
                 if '"moviebackground"' in data:
                     fanart_2=scrapertools.get_match(data,'"moviebackground":.*?"url": "([^"]+)"')
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
                        show=  item.extra
                        if '"moviebanner"' in data:
                             category= banner
                        else:
                            category= item.extra
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_pelis", url=item.url,  thumbnail=logo, fanart=item.extra,category= category, extra=extra,show=show ,  folder=True) )
    if "_serie_de_tv" in item.url:
        title= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
        title = title.replace("(Serie de TV)","")
        title = title.replace("torrent","")
        title= title.replace(' ','%20')
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
            plot = item.plot
            category= ""
            itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos", thumbnail=item.thumbnail, fanart=item.thumbnail ,extra=extra, category= category,  show=show , folder=True) )
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
                    itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos", thumbnail=item.thumbnail, fanart=item.thumbnail ,category = category, extra=extra, show=show, folder=True) )
                        
            for fan in matches:
                fanart="http://thetvdb.com/banners/" + fan
                item.extra= fanart
            #clearart, fanart_2 y logo
            for id in matches:
                url ="http://assets.fanart.tv/v3/tv/"+id_serie+"?api_key=6fa42b0ef3b5f3aab6a7edaa78675ac2"
                if "Castle" in title:
                    url ="http://assets.fanart.tv/v3/tv/83462?api_key=6fa42b0ef3b5f3aab6a7edaa78675ac2"
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
                            fanart_2=scrapertools.get_match(data,'"showbackground":.*?"url": "([^"]+)"')
                            if '"hdclearart"' in data:
                                 thumbnail = hdtvlogo
                                 extra=  hdtvclear
                                 show = fanart_2
                            else:
                                thumbnail = hdtvlogo
                                extra= thumbnail
                                show = fanart_2
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, category=category, extra=extra, show=show, folder=True) )
                        
                        
                        else:
                            if '"hdclearart"' in data:
                                thumbnail= hdtvlogo
                                extra= hdtvclear
                                show= item.extra
                            else:
                                thumbnail= hdtvlogo
                                extra= thumbnail
                                show= item.extra
                            
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra, show=show,  category= category, folder=True) )
                    else:
                         extra=  item.thumbnail
                         show = item.extra
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=item.thumbnail, fanart=item.extra, extra=extra, show=show, category = category, folder=True) )
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
                        fanart_2=scrapertools.get_match(data,'"showbackground":.*?"url": "([^"]+)"')
                        extra=clear
                        show= fanart_2
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show, category= category,  folder=True) )
                    else:
                        extra= clear
                        show=item.extra
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
        
                if "showbackground" in data:
                    fanart_2=scrapertools.get_match(data,'"showbackground":.*?"url": "([^"]+)"')
                    if '"clearart"' in data:
                         clear=scrapertools.get_match(data,'"clearart":.*?"url": "([^"]+)"')
                         extra=clear
                         show= fanart_2
                    else:
                         extra=logo
                         show= fanart_2
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show,  category = category, folder=True) )
                
                if not '"clearart"' in data and not '"showbackground"' in data:
                        if '"hdclearart"' in data:
                            extra= hdtvclear
                            show= item.extra
                        else:
                             extra= thumbnail
                             show=  item.extra
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show , category = category, folder=True) )


    title ="Info"
    if len(item.extra)==0:
        fanart=item.thumbnail
    else:
        fanart = item.extra
    
    if '"movieposter"' in data:
         thumbnail= poster
    elif '"moviethumb"' in data:
          thumbnail = thumb
    
    else:
         thumbnail = item.thumbnail
    title = title.replace(title,"[COLOR skyblue]"+title+"[/COLOR]")
    itemlist.append( Item(channel=__channel__, action="info" , title=title , url=item.url, thumbnail=thumbnail, fanart=fanart, extra = extra, show = show,folder=False ))
    ###trailer
   
   
    title= "[COLOR crimson]Trailer[/COLOR]"
    if len(item.extra)==0:
        fanart=item.thumbnail
    else:
        fanart = item.extra

    if '"moviethumb"' in data:
        thumbnail = thumb
    elif '"tvthumb"' in data:
          thumbnail = tvthumb
    else:
          thumbnail = item.thumbnail
    if '"moviedisc"' in data:
        extra= disc
    elif '"tvbanner"' in data:
           extra= tvbanner
    else:
          if '"moviethumb"' in data:
                extra = thumb
          elif '"tvthumb"' in data:
                 extra = tvthumb
          else:
                   extra = item.thumbnail


    itemlist.append( Item(channel=__channel__, action="trailer", title=title , url=item.url , thumbnail=thumbnail , plot=item.plot , fanart=fanart, extra=extra, folder=True) )

    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.bityouth search")
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

    show = item.category+"|"+item.thumbnail+"|"+id
    title ="Info"
    title = title.replace(title,"[COLOR skyblue]"+title+"[/COLOR]")
    itemlist.append( Item(channel=__channel__, action="info_capitulos" , title=title , url=item.url, thumbnail=thumbnail, fanart=fanart, extra = item.extra, show = show, folder=False ))

    return itemlist
def findvideos_pelis(item):
    logger.info("pelisalacarta.bityouth search")
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
    api_google_for_trailer = "https://www.google.com/uds/GvideoSearch?callback=google.search.VideoSearch.RawCompletion&rsz=small&hl=es&source=gsc&gss=.com&sig=cb6ef4de1f03dde8c26c6d526f8a1f35&q=site%3Ahttp%3A%2F%2Fyoutube.com%20" + item.plot + "&qid=14e3123d9b6320389&context=0&key=notsupplied&v=1.0"
    
    data = scrapertools.cache_page(api_google_for_trailer).replace('\\u003d','=').replace('\\u0026','&')
    
    patron = '"title":"([^"]+)".*?'
    patron+= '"tbUrl":"([^"]+)".*?'
    patron+= '"url":"([^"]+)"'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    if len(matches)==0 :
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]No hay Trailer[/B][/COLOR]", thumbnail ="http://s6.postimg.org/jp5jx97ip/bityoucancel.png", fanart ="http://s6.postimg.org/vfjhen0b5/bityounieve.jpg",folder=False) )
    
    for scrapedtitle, scrapedthumbnail, scrapedurl in matches:
        scrapedtitle=re.sub(r"\n|\r|\t|\s{2}|&.*?;","",scrapedtitle)
        scrapedtitle=scrapedtitle.replace(scrapedtitle,"[COLOR sandybrown][B]"+scrapedtitle+"[/B][/COLOR]")
        itemlist.append( Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, server="youtube", fanart="http://s23.postimg.org/84vkeq863/movietrailers.jpg", thumbnail=item.extra, action="play", folder=False) )

    return itemlist

def play(item):
    logger.info("pelisalacarta.bityouth search")
    itemlist = []
    
    if item.server == "youtube":
        itemlist.append( Item(channel=__channel__, title=item.plot, url=item.url, server="youtube", fanart=item.fanart, thumbnail=item.thumbnail, action="play", folder=False) )
    
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    patron = '<td><a class="btn btn-success" href="([^"]+)"'
    
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    for scrapedurl in matches:
        
       
        itemlist.append( Item(channel=__channel__, title=item.title, server="torrent", url=scrapedurl, fanart="http://s9.postimg.org/lmwhrdl7z/aquitfanart.jpg", thumbnail="http://s6.postimg.org/4hpbrb13l/texflecha2.png", action="play", folder=True) )
    
    
    
    return itemlist

def info(item):
    logger.info("pelisalacarta.sinluces trailer")
    url=item.url
    data = scrapertools.cachePage(url)
    data = re.sub(r"\n|\r|\t|\s{2}|&.*?;","",data)
    title= scrapertools.get_match(data,'<meta name="title" content="(.*?) -')
    title = title.replace(title,"[COLOR aqua][B]"+title+"[/B][/COLOR]")
    title = title.replace("torrent","")
    plot = scrapertools.get_match(data,'<div itemprop="description">(.*?)</div>')
    plot = plot.replace(plot,"[COLOR white][B]"+plot+"[/B][/COLOR]")
    plot = plot.replace("</i>","")
    plot = plot.replace("</br>","")
    plot = plot.replace("<br/>","")
    plot = plot.replace("&#8220","")
    plot = plot.replace("<b>","")
    plot = plot.replace("</b>","")
    plot = plot.replace(" &#8203;&#8203;","")
    plot = plot.replace("&#8230","")
    
    
    foto = item.show
    photo= item.extra
    
    ventana2 = TextBox1(title=title, plot=plot, thumbnail=photo, fanart=foto)
    ventana2.doModal()

class TextBox1( xbmcgui.WindowDialog ):
         """ Create a skinned textbox window """
         def __init__( self, *args, **kwargs):
            
            self.getTitle = kwargs.get('title')
            self.getPlot = kwargs.get('plot')
            self.getThumbnail = kwargs.get('thumbnail')
            self.getFanart = kwargs.get('fanart')
                            
            self.background = xbmcgui.ControlImage( 70, 20, 1150, 630, 'http://s6.postimg.org/58jknrvtd/backgroundventana5.png')
            self.title = xbmcgui.ControlTextBox(140, 60, 1130, 50)
            self.plot = xbmcgui.ControlTextBox( 140, 140, 1035, 600 )
            self.thumbnail = xbmcgui.ControlImage( 813, 43, 390, 100, self.getThumbnail )
            self.fanart = xbmcgui.ControlImage( 140, 351, 1035, 250, self.getFanart )
                                                
            self.addControl(self.background)
            self.addControl(self.title)
            self.addControl(self.plot)
            self.addControl(self.thumbnail)
            self.addControl(self.fanart)
                
            self.title.setText( self.getTitle )
            self.plot.setText(  self.getPlot )
                
         def get(self):
             self.show()
                
         def onAction(self, action):
             self.close()

def test():
    return True

def info_capitulos(item):
    logger.info("pelisalacarta.bricocine info_capitulos")
    item.category = item.show.split("|")[0]
    item.thumbnail = item.show.split("|")[1]
    id = item.show.split("|")[2]
    url="https://www.themoviedb.org/tv/"+item.show.split("|")[2]+item.extra.split("|")[1]+"/season/"+item.extra.split("|")[0]+"/episode/"+item.extra.split("|")[2]+"?language=en"
    data = scrapertools.cachePage(url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = '<p><strong>Air Date:</strong>.*?content="(.*?)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)==0 :
        title = "[COLOR red][B]LO SENTIMOS...[/B][/COLOR]"
        plot = "Este capitulo no tiene informacion..."
        plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
        foto = "http://s6.postimg.org/nm3gk1xox/noinfosup2.png"
        image="http://s6.postimg.org/ub7pb76c1/noinfo.png"

    for day in matches:
        url="http://thetvdb.com/api/GetEpisodeByAirDate.php?apikey=1D62F2F90030C444&seriesid="+item.show.split("|")[0]+"&airdate="+day+"&language=es"
        if "%20Castle%20" in item.extra.split("|")[1]:
            url="http://thetvdb.com/api/GetEpisodeByAirDate.php?apikey=1D62F2F90030C444&seriesid=83462"+"&airdate="+day+"&language=es"
        
        data = scrapertools.cachePage(url)
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
        patron = '<Data>.*?<EpisodeName>([^<]+)</EpisodeName>.*?'
        patron += '<Overview>(.*?)</Overview>.*?'
        
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)==0 :
            title = "[COLOR red][B]LO SENTIMOS...[/B][/COLOR]"
            plot = "Este capitulo no tiene informacion..."
            plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
            image="http://s6.postimg.org/ub7pb76c1/noinfo.png"
            foto="http://s6.postimg.org/nm3gk1xox/noinfosup2.png"
    
        else :
            
            
            for name_epi, info in matches:
                if "<filename>episodes" in data:
                    foto = scrapertools.get_match(data,'<Data>.*?<filename>(.*?)</filename>')
                    fanart = "http://thetvdb.com/banners/" + foto
                else:
                     fanart=item.show.split("|")[1]
                                    
                plot = info
                plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
                title = name_epi.upper()
                title = title.replace(title,"[COLOR skyblue][B]"+title+"[/B][/COLOR]")
                image=fanart
                foto= item.show.split("|")[1]
    ventana = TextBox2(title=title, plot=plot, thumbnail=image, fanart=foto)
    ventana.doModal()




class TextBox2( xbmcgui.WindowDialog ):
        """ Create a skinned textbox window """
        def __init__( self, *args, **kwargs):
            self.getTitle = kwargs.get('title')
            self.getPlot = kwargs.get('plot')
            self.getThumbnail = kwargs.get('thumbnail')
            self.getFanart = kwargs.get('fanart')
            
            self.background = xbmcgui.ControlImage( 70, 20, 1150, 630, 'http://s6.postimg.org/n3ph1uxn5/ventana.png')
            self.title = xbmcgui.ControlTextBox(120, 60, 430, 50)
            self.plot = xbmcgui.ControlTextBox( 120, 150, 1056, 100 )
            self.thumbnail = xbmcgui.ControlImage( 120, 300, 1056, 300, self.getThumbnail )
            self.fanart = xbmcgui.ControlImage( 780, 43, 390, 100, self.getFanart )
            
            self.addControl(self.background)
            self.addControl(self.title)
            self.addControl(self.plot)
            self.addControl(self.thumbnail)
            self.addControl(self.fanart)
            
            self.title.setText( self.getTitle )
            self.plot.setText(  self.getPlot )
        
        def get(self):
            self.show()
        
        def onAction(self, action):
            self.close()
def test():
    return True





