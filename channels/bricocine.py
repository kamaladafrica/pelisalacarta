    # -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

import xbmcgui


__channel__ = "bricocine"
__category__ = "F"
__type__ = "generic"
__title__ = "bricocine"
__language__ = "ES"

DEBUG = config.get_setting("debug")
## Cargar los datos con la librería 'requests'
def get_page( url ):
    
    from lib import requests
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()
    response = requests.get( url )
    return response.content

def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.bricocine mainlist")

    itemlist = []
    itemlist.append( Item(channel=__channel__, title="[COLOR sandybrown][B]Pelis MicroHD[/B][/COLOR]"      , action="peliculas", url="http://www.bricocine.com/c/hd-microhd/", thumbnail="http://s6.postimg.org/5vgi38jf5/HD_brico10.jpg", fanart="http://s16.postimg.org/6g9tc2nyt/brico_pelifan.jpg"))
    itemlist.append( Item(channel=__channel__, title="[COLOR sandybrown][B]Pelis Bluray-Rip[/B][/COLOR]" , action="peliculas", url="http://www.bricocine.com/c/bluray-rip/",  thumbnail="http://s6.postimg.org/5w82dorpt/blueraybrico.jpg", fanart="http://i59.tinypic.com/11rdnjm.jpg"))
    itemlist.append( Item(channel=__channel__, title="[COLOR sandybrown][B]Pelis DVD-Rip[/B][/COLOR]" , action="peliculas", url="http://www.bricocine.com/c/dvdrip/", thumbnail="http://s6.postimg.org/d2dlld4y9/dvd2.jpg", fanart="http://s6.postimg.org/hcehbq5w1/brico_blue_fan.jpg"))
    itemlist.append( Item(channel=__channel__, title="[COLOR sandybrown][B]Pelis 3D[/B][/COLOR]" , action="peliculas", url="http://www.bricocine.com/c/3d/", thumbnail="http://www.eias3d.com/wp-content/uploads/2011/07/3d2_5.png", fanart="http://s6.postimg.org/u18rvec0h/bric3dd.jpg"))
    import xbmc, time
    if xbmc.Player().isPlaying():
       xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
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
    
    itemlist.append( Item(channel=__channel__, title="[COLOR sandybrown][B]Series[/B][/COLOR]"         , action="peliculas", url="http://www.bricocine.com/c/series", thumbnail="http://img0.mxstatic.com/wallpapers/bc795faa71ba7c490fcf3961f3b803bf_large.jpeg", fanart="http://s6.postimg.org/z1ath370x/bricoseries.jpg"))
    import xbmc, time
    if xbmc.Player().isPlaying():
       xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
    KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
    REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
    APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
    SEARCHDESTFILE= os.path.join(xbmc.translatePath('special://userdata/keymaps'), "search.txt")
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
    itemlist.append( Item(channel=__channel__, title="[COLOR sandybrown][B]Buscar[/B][/COLOR]"         , action="search", url="", thumbnail="http://fc04.deviantart.net/fs70/i/2012/285/3/2/poltergeist___tv_wallpaper_by_elclon-d5hmmlp.png", fanart="http://s6.postimg.org/f44w84o5t/bricosearch.jpg", extra = "search"))
    

    return itemlist


def search(item,texto):
    logger.info("pelisalacarta.bricocine search")
    texto = texto.replace(" ","+")
    item.url = "http://www.bricocine.com/index.php/?s=%s" % (texto)
    try:
        return peliculas(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def peliculas(item):
    logger.info("pelisalacarta.bricocine peliculas")
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

    # Descarga la página
    data = get_page( item.url )
    '''
   <div class="post-10888 post type-post status-publish format-standard hentry category-the-leftovers tag-ciencia-ficcion tag-drama tag-fantasia tag-misterio"><div class="entry"> <a href="http://www.bricocine.com/10888/leftovers-temporada-1/"> <img src="http://www.bricocine.com/wp-content/plugins/wp_movies/files/thumb_185_the_leftovers_.jpg" alt="The Leftovers " /> </a></div><div class="entry-meta"><div class="clearfix"><div itemprop="aggregateRating" itemscope itemtype="http://schema.org/AggregateRating" class="rating"  title="Puntos IMDB: 7.4"><div class="rating-stars imdb-rating"><div class="stars" style="width:74%"></div></div><div itemprop="ratingValue" class="rating-number"> 7.4</div></div><div itemprop="aggregateRating" itemscope itemtype="http://schema.org/AggregateRating" class="rating"  title="Puntos Bricocine: 6.2"><div class="rating-stars brico-rating"><div class="stars" style="width:62%"></div></div><div itemprop="ratingValue" class="rating-number"> 6.2</div></div> <span class="vcard author none"> Publicado por <a class="fn" href="" rel="author" target="_blank"></a> </span> <span class="date updated none">2014-10-07T23:36:17+00:00</span></div></div><h2 class="title2 entry-title"> <a href="http://www.bricocine.com/10888/leftovers-temporada-1/"> The Leftovers  &#8211; Temporada 1 </a></h2></div> </article> <article class="hentry item-entry"><div class="post-10088 post type-post status-publish format-standard hentry category-the-last-ship tag-accion tag-ciencia-ficcion tag-drama tag-the tag-thriller"><div class="entry"> <a href="http://www.bricocine.com/10088/last-ship-temporada-1/"> <img src="http://www.bricocine.com/wp-content/plugins/wp_movies/files/thumb_185_the_last_ship_.jpg" alt="The Last Ship " /> </a></div><div class="entry-meta"><div class="clearfix"><div itemprop="aggregateRating" itemscope itemtype="http://schema.org/AggregateRating" class="rating"  title="Puntos IMDB: 7.4"><div class="rating-stars imdb-rating"><div class="stars" style="width:74%"></div></div><div itemprop="ratingValue" class="rating-number"> 7.4</div></div><div itemprop="aggregateRating" itemscope itemtype="http://schema.org/AggregateRating" class="rating"  title="Puntos Bricocine: 7.0"><div class="rating-stars brico-rating"><div class="stars" style="width:70%"></div></div><div itemprop="ratingValue" class="rating-number"> 7.0</div></div> <span class="vcard author none"> Publicado por <a class="fn" href="" rel="author" target="_blank"></a> </span> <span class="date updated none">2014-10-07T23:32:25+00:00</span></div></div><h2 class="title2 entry-title"> <a href="http://www.bricocine.com/10088/last-ship-temporada-1/"> The Last Ship &#8211; Temporada 1 </a></h2></div> </article> <article class="hentry item-entry">

    '''
    
    patron = '<div class="entry"> '
    patron += '<a href="([^"]+)"> '
    patron += '<img src="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += 'class="rating-number">([^<]+)</div></div>'

    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    if len(matches)==0 :
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]No hay resultados...[/B][/COLOR]", thumbnail ="http://s6.postimg.org/fay99h9ox/briconoisethumb.png", fanart ="http://s6.postimg.org/uie8tu1jl/briconoisefan.jpg",folder=False) )

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedcreatedate in matches:
        scrapedcreatedate = scrapedcreatedate.replace(scrapedcreatedate,"[COLOR sandybrown][B]"+scrapedcreatedate+"[/B][/COLOR]")
        scrapedtitle = scrapedtitle.replace(scrapedtitle,"[COLOR white]"+scrapedtitle+"[/COLOR]")
        scrapedtitle = scrapedtitle + "(Puntuación:" + scrapedcreatedate + ")"
        title = scrapedtitle
        if "index" in item.url:
             if "temporada" in scrapedurl:
                 title = scrapedurl
                 title= re.sub(r"\http://.*?/.*?/|/|&nbsp;","",title)
                 title= title.replace("-"," ")
                 title = title.capitalize()
                 title= title.replace("temporada","[COLOR green]Temporada[/COLOR]")
                 title = title.replace	(title,"[COLOR white]"+title+"[/COLOR]")
                 title = title + "(Puntuación:" + scrapedcreatedate + ")"
                 if item.extra == "search":
                     import xbmc
                     SEARCHDESTFILE= os.path.join(xbmc.translatePath('special://userdata/keymaps'), "search.txt")
                     urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/search.txt", SEARCHDESTFILE )
        
        itemlist.append( Item(channel=__channel__, title=title, url=scrapedurl, action="fanart", thumbnail=scrapedthumbnail, fanart="http://s15.postimg.org/id6ec47vf/bricocinefondo.jpg",  folder=True) )

    
    ## Paginación
    #<span class='current'>1</span><a href='http://www.bricocine.com/c/hd-microhd/page/2/'
    
    # Si falla no muestra ">> Página siguiente"
    try:
        next_page = scrapertools.get_match(data,"<span class='current'>\d+</span><a href='([^']+)'")
        title= "[COLOR red]Pagina siguiente>>[/COLOR]"
        itemlist.append( Item(channel=__channel__, title=title, url=next_page, action="peliculas", fanart="http://s15.postimg.org/id6ec47vf/bricocinefondo.jpg", thumbnail="http://s7.postimg.org/w2e0nr7hn/pdksiguiente.jpg", folder=True) )
    except: pass
    
    return itemlist



def fanart(item):
    #Vamos a sacar todos los fanarts y arts posibles
    logger.info("pelisalacarta.bricocine fanart")
    itemlist = []
    url = item.url
    data = get_page( item.url )
    data = re.sub(r"\n|\r|\t|\s{2}|\(.*?\)|\[.*?\]|&nbsp;","",data)
    
    if "temporada" in item.url:
        import xbmc
        
        SEARCHDESTFILE= os.path.join(xbmc.translatePath('special://userdata/keymaps'), "search.txt")
        TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
        KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
        REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
        APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
        TRAILERDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "trailer.txt")
        
           
        title= scrapertools.get_match(data,'<title>(.*?) -')
        title= re.sub(r"3D|,|#|;|SBS|-|","",title)
        title= title.replace('Temporada','')
        title= title.replace('Torrent','')
        title= title.replace('á','a')
        title= title.replace('Á','A')
        title= title.replace('é','e')
        title= title.replace('í','i')
        title= title.replace('ó','o')
        title= title.replace('ú','u')
        title= title.replace('ñ','n')
        title= title.replace('Fin','')
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
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/test.py", TESTPYDESTFILE )
                   KEYMAPDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customkey.xml")
        
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/customkey.xml", KEYMAPDESTFILE )
                   REMOTEDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remote.xml")
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/remote.xml", REMOTEDESTFILE )
                   APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
                   urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/customapp.xml", APPCOMMANDDESTFILE )
                
                   xbmc.executebuiltin('Action(reloadkeymaps)')
              
               except:
                   pass
        try:
            os.remove(TRAILERDESTFILE)
            print "Trailer.txt borrado"
        except:
            print "No hay Trailer.txt"
        
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
                xbmc.executebuiltin('Action(reloadkeymaps)')
                print "No hay customs"

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
                    fanart_info = item.thumbnail
                    fanart_trailer = item.thumbnail
                    itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos", thumbnail=item.thumbnail, fanart=item.thumbnail ,category = category, extra=extra, show=show,folder=True) )

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
                    url ="http://webservice.fanart.tv/v3/tv/83462?api_key=dffe90fba4d02c199ae7a9e71330c987"
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
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, category=category, extra=extra, show=show, folder=True) )
                                
    
                        else:
                            if '"hdclearart"' in data:
                                thumbnail= hdtvlogo
                                extra= hdtvclear
                                show= fanart_2
                            else:
                                thumbnail= hdtvlogo
                                extra= thumbnail
                                show= fanart_2
                            
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra, show=show,  category= category, folder=True) )
                    else:
                        extra=  item.thumbnail
                        show = fanart_2
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
                        
                        extra=clear
                        show= fanart_2
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
                    else:
                         extra= clear
                         show=fanart_2
                         itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
                
                if "showbackground" in data:
                    
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
                            show= fanart_2
                        else:
                            extra= thumbnail
                            show=  fanart_2
                        itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos", url=item.url, server="torrent", thumbnail=thumbnail, fanart=item.extra, extra=extra,show=show , category = category, folder=True) )
                
    else:
            title= scrapertools.get_match(data,'<title>(.*?)Torrent')
            title= re.sub(r"3D|SBS|\(.*?\)|\[.*?\]|-|","",title)
            title= title.replace('á','a')
            title= title.replace('é','e')
            title= title.replace('í','i')
            title= title.replace('ó','o')
            title= title.replace('ú','u')
            title= title.replace('Torrent','')
            title= title.replace(' ','%20')
            url="http://api.themoviedb.org/3/search/movie?api_key=57983e31fb435df4df77afb854740ea9&query=" + title + "&language=es&include_adult=false"
            data = get_page( url )
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
                itemlist.append( Item(channel=__channel__, title=item.title, url=item.url, action="findvideos_peli", thumbnail=item.thumbnail, fanart=item.thumbnail ,extra=extra, show=show, category= category, folder=True) )
            
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
                    data = get_page( url )
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
                       extra= posterdb
                       show = fanart_2
                       category = item.extra
                       itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_peli", url=item.url, server="torrent", thumbnail=posterdb, fanart=item.extra,  extra=extra, show=show, category= category, folder=True) )
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
                             itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_peli", url=item.url, server="torrent", thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )
                         else:
                             extra= clear
                             show=fanart_2
                             if '"moviebanner"' in data:
                                 category = banner
                             else:
                                 category = clear
                             itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_peli", url=item.url, server="torrent", thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category, folder=True) )

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
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_peli", url=item.url, server="torrent", thumbnail=logo, fanart=item.extra, extra=extra,show=show, category= category,  folder=True) )
        
                    if not '"hdmovieclearart"' in data and not '"moviebackground"' in data:
                            extra= logo
                            show=  fanart_2
                            if '"moviebanner"' in data:
                                category= banner
                            else:
                                category= item.extra
                            itemlist.append( Item(channel=__channel__, title = item.title , action="findvideos_peli", url=item.url, server="torrent", thumbnail=logo, fanart=item.extra,category= category, extra=extra,show=show ,  folder=True) )
    
    title ="Info"
    title = title.replace(title,"[COLOR skyblue]"+title+"[/COLOR]")
    if not "temporada" in item.url:
       thumbnail = posterdb
    if "temporada" in item.url:
        if '"tvposter"' in data:
            thumbnail= tvposter
        else:
            thumbnail = item.thumbnail
        
        if "tvbanner" in data:
            category = tvbanner
        else:
            category = show


    itemlist.append( Item(channel=__channel__, action="info" , title=title , url=item.url, thumbnail=thumbnail, fanart=fanart_info, show= show, extra= extra, category= category, folder=False ))


    title= "[COLOR crimson]Trailer[/COLOR]"
    
    if len(item.extra)==0:
       fanart=item.thumbnail
    else:
        fanart = item.extra

    if "temporada" in item.url:
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



    itemlist.append( Item(channel=__channel__, action="trailer", title=title , url=item.url , thumbnail=thumbnail , fulltitle = item.title , fanart=fanart_trailer, extra=extra, folder=True) )

    return itemlist
def findvideos(item):
    logger.info("pelisalacarta.bricocine findvideos")
    
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

    data = get_page( item.url )
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
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
    

    

    #id_torrent = scrapertools.get_match(item.url,"(\d+)-")
    
    patron = '<span class="title">([^<]+)- (\d)(\d+)([^<]+).*?'
    patron += 'id="([^"]+)" href="([^"]+)".*?'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)==0:
        show = item.show
        extra = item.extra
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]Ooops!! Algo no va bien,pulsa para ser dirigido a otra busqueda, ...[/B][/COLOR]",action="findvideos_peli", url=item.url, thumbnail ="http://s6.postimg.org/fay99h9ox/briconoisethumb.png", fanart ="http://s6.postimg.org/uie8tu1jl/briconoisefan.jpg", extra=extra, show=show, folder=True) )
    
    import base64
    for title_links, seasson, epi, calidad, title_torrent, url_torrent in matches:
        ## torrent
        season=scrapertools.get_match(data,'<title>.*?Temporada.*?(\d+).*?Torrent')
        epi=re.sub(r"101|201|301|401|501|601|701|801|901","01",epi)
        epi=re.sub(r"102|202|302|402|502|602|702|802|902","02",epi)
        epi=re.sub(r"103|203|303|403|503|603|703|803|903","03",epi)
        epi=re.sub(r"104|204|304|404|504|604|704|804|904","04",epi)
        epi=re.sub(r"105|205|305|405|505|605|705|805|905","05",epi)
        epi=re.sub(r"106|206|306|406|506|606|706|806|906","06",epi)
        epi=re.sub(r"107|207|307|407|507|607|707|807|907","07",epi)
        epi=re.sub(r"108|208|308|408|508|608|708|808|908","08",epi)
        epi=re.sub(r"109|209|309|409|509|609|709|809|909","09",epi)
        epi=re.sub(r"110|210|310|410|510|610|710|810|910","10",epi)
        epi=re.sub(r"111|211|311|411|511|611|711|811|911","11",epi)
        epi=re.sub(r"112|212|312|412|512|612|712|812|912","12",epi)
        epi=re.sub(r"113|213|313|413|513|613|713|813|913","13",epi)
        epi=re.sub(r"114|214|314|414|514|614|714|814|914","14",epi)
        epi=re.sub(r"115|215|315|415|515|615|715|815|915","15",epi)
        epi=re.sub(r"116|216|316|416|516|616|716|816|916","16",epi)
        epi=re.sub(r"117|217|317|417|517|617|717|817|917","17",epi)
        epi=re.sub(r"118|218|318|418|518|618|718|818|918","18",epi)
        epi=re.sub(r"119|219|319|419|519|619|719|819|919","19",epi)
        epi=re.sub(r"120|220|320|420|520|620|720|820|920","20",epi)
        epi=re.sub(r"121|221|321|421|521|621|721|821|921","21",epi)
        epi=re.sub(r"122|222|322|422|522|622|722|822|922","22",epi)
        epi=re.sub(r"123|223|323|423|523|623|723|823|923","23",epi)
        epi=re.sub(r"124|224|324|424|524|624|724|824|924","24",epi)
        epi=re.sub(r"125|225|325|425|525|625|725|825|925","25",epi)
        epi=re.sub(r"126|226|326|426|526|626|726|826|926","26",epi)
        epi=re.sub(r"127|227|327|427|527|627|727|827|927","27",epi)
        epi=re.sub(r"128|228|328|428|528|628|728|828|928","28",epi)
        epi=re.sub(r"129|229|329|429|529|629|729|829|929","29",epi)
        epi=re.sub(r"130|230|330|430|530|630|730|830|930","30",epi)
        
        seasson_epi = season+"x"+epi
        seasson_epi = seasson_epi.replace(seasson_epi,"[COLOR sandybrown]"+seasson_epi+"[/COLOR]")
        if "x0" in seasson_epi:
            epi = epi.replace("0","")
        title_torrent = "["+title_torrent.replace("file","torrent")+"]"
        title_torrent = title_torrent.replace(title_torrent,"[COLOR green]"+title_torrent+"[/COLOR]")
        calidad = calidad.replace(calidad,"[COLOR sandybrown]"+calidad+"[/COLOR]")
        title_links = title_links.replace(title_links,"[COLOR orange]"+title_links+"[/COLOR]")
        title_torrent = title_links+" "+seasson_epi+calidad+"- "+title_torrent
        url_torrent = base64.decodestring(url_torrent.split('&u=')[1][::-1])
        title_links = re.sub(r"\n|\r|\t|\s{2}|\(.*?\)|\[.*?\]|&nbsp;","",title_links)
        title_links= title_links.replace('\[.*?\]','')
        title_links= title_links.replace('á','a')
        title_links= title_links.replace('Á','A')
        title_links= title_links.replace('é','e')
        title_links= title_links.replace('í','i')
        title_links= title_links.replace('ó','o')
        title_links= title_links.replace('ú','u')
        title_links= title_links.replace(' ','%20')
        extra = season+"|"+title_links+"|"+epi
        itemlist.append( Item(channel=__channel__, title = title_torrent , action="episodios", url=url_torrent, thumbnail=item.extra, fanart=item.show, extra=extra, category= item.category, folder=True) )

    return itemlist

def episodios(item):
    logger.info("pelisalacarta.bricocine episodios")
    itemlist = []
    import xbmc, time
    TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
    if os.path.exists ( TESTPYDESTFILE ):
        TRAILERDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "trailer.txt")
        urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/trailer.txt", TRAILERDESTFILE )
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
    title_links = item.extra.split("|")[1]
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
        itemlist.append( Item(channel=__channel__, title = title , action="play", url=item.url, thumbnail=thumbnail, fanart=fanart,  folder=False) )

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
           itemlist.append( Item(channel=__channel__, title = title , action="play", url=item.url, thumbnail=thumbnail, fanart=fanart,  folder=False) )
        for foto in matches:
            thumbnail = "https://image.tmdb.org/t/p/original" + foto
            
            extra = id+"|"+season
            itemlist.append( Item(channel=__channel__, title = title , action="play", url=item.url, thumbnail=thumbnail, fanart=fanart,  category = item.category, folder=False) )
    ###thumb temporada###
    url= "http://api.themoviedb.org/3/tv/"+id+"/season/"+season+"/images?api_key=57983e31fb435df4df77afb854740ea9"
    data = get_page( url )
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = '{"id".*?"file_path":"(.*?)","height"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches) == 0:
       thumbnail= item.thumbnail
    for temp in matches:
        thumbnail= "https://image.tmdb.org/t/p/original"+ temp
    ####fanart info####
    url ="http://api.themoviedb.org/3/tv/"+id+"/images?api_key=57983e31fb435df4df77afb854740ea9"
    data = get_page( url )
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = '{"backdrops".*?"file_path":".*?","height".*?"file_path":"(.*?)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches) == 0:
        fanart = item.fanart
    for fanart_4 in matches:
        fanart = "https://image.tmdb.org/t/p/original" + fanart_4
    show = item.category+"|"+item.thumbnail

    title ="Info"
    title = title.replace(title,"[COLOR skyblue]"+title+"[/COLOR]")
    itemlist.append( Item(channel=__channel__, action="info_capitulos" , title=title , url=item.url, thumbnail=thumbnail, fanart=fanart, extra = item.extra, show = show, folder=False ))


    return itemlist
def play(item):
    logger.info("pelisalacarta.bricocine play")
    itemlist = []
    if "youtube" in item.url:
        itemlist.append( Item(channel=__channel__, action="play", server="youtube",  url=item.url ,  fulltitle = item.title , fanart="http://s23.postimg.org/84vkeq863/movietrailers.jpg", folder=False) )
    

    itemlist.append( Item(channel=__channel__, title = item.title , action="play", url=item.url, server="torrent", thumbnail=item.thumbnail, fanart=item.fanart,  category = item.category, folder=False) )


    return itemlist




def findvideos_peli(item):
    logger.info("pelisalacarta.bricocine findvideos_peli")
    
    itemlist = []
    data = get_page( item.url )
   
    
    #id_torrent = scrapertools.get_match(item.url,"(\d+)-")
    
    patron = '<span class="title">([^"]+)</span>.*?'
    patron += 'id="([^"]+)" href="([^"]+)".*?'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)==0 :
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]El video ya no se encuentra en la web, prueba a encontrala por busqueda...[/B][/COLOR]", thumbnail ="http://s6.postimg.org/fay99h9ox/briconoisethumb.png", fanart ="http://s6.postimg.org/uie8tu1jl/briconoisefan.jpg",folder=False) )
    import base64
    for title_links, title_torrent, url_torrent in matches:
        ## torrent
        title_torrent = "["+title_torrent.replace("file","torrent")+"]"
        title_torrent = title_torrent.replace(title_torrent,"[COLOR green]"+title_torrent+"[/COLOR]")
        title_links = title_links.replace(title_links,"[COLOR sandybrown]"+title_links+"[/COLOR]")
        title_links = re.sub(r"&#.*?;","",title_links)
        title_tag="[COLOR yellow]Ver --[/COLOR]"
        title_torrent = title_tag+title_links+"- "+title_torrent
        url_torrent = base64.decodestring(url_torrent.split('&u=')[1][::-1])
        itemlist.append( Item(channel=__channel__, title = title_torrent , action="play", url=url_torrent, server="torrent", thumbnail=item.extra, fanart=item.show,  folder=False) )


    return itemlist
def trailer(item):
    
    logger.info("pelisalacarta.bricocine trailer")
    import xbmc
    if  xbmc.Player().isPlaying():
        TRAILERDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "trailer.txt")
        urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/trailer.txt", TRAILERDESTFILE )
    
    itemlist = []
    data = get_page( item.url )
    
    
    #trailer
    patron = "<iframe width='.*?' height='.*?' src='([^']+)?"
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)==0 :
        itemlist.append( Item(channel=__channel__, title="[COLOR gold][B]Esta pelicula no tiene trailer,lo sentimos...[/B][/COLOR]", thumbnail ="http://s6.postimg.org/fay99h9ox/briconoisethumb.png", fanart ="http://s6.postimg.org/uie8tu1jl/briconoisefan.jpg",folder=False) )
    
    for url in matches:
        listavideos = servertools.findvideos(url)

        for video in listavideos:
            videotitle = scrapertools.unescape(video[0])
            url =video [1]
            server = video[2]
        
        #xbmctools.addnewvideo( __channel__ , "play" , category , server ,  , url , thumbnail , plot )
        title= "[COLOR crimson]Trailer - [/COLOR]"
        itemlist.append( Item(channel=__channel__, action="play", server="youtube", title=title + videotitle   , url=url , thumbnail=item.extra ,  fulltitle = item.title , fanart="http://s23.postimg.org/84vkeq863/movietrailers.jpg", folder=False) )
    return itemlist

def info(item):
    
    logger.info("pelisalacarta.bricocine info")
    url=item.url
    data = get_page( url )
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    if "temporada" in item.url:
      import xbmc
      APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
      try:
         os.remove(APPCOMMANDDESTFILE)
      except:
         pass
      patron ='<title>([^<]+).*?Temporada.*?'
      patron += '<div class="description" itemprop="text.*?">.*?([^<]+).*?</div></div></div>'
      matches = re.compile(patron,re.DOTALL).findall(data)
      if len(matches)==0 :
          title = "[COLOR red][B]LO SENTIMOS...[/B][/COLOR]"
          plot = "Esta serie no tiene informacion..."
          plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
          photo="http://s6.postimg.org/nm3gk1xox/noinfosup2.png"
          foto ="http://s6.postimg.org/ub7pb76c1/noinfo.png"
          info =""
          quit = "Pulsa"+" [COLOR crimson][B]INTRO [/B][/COLOR]"+ "para quitar"
      for title, plot in matches:
          plot_title = "Sinopsis" + "[CR]"
          plot_title = plot_title.replace(plot_title,"[COLOR red]"+plot_title+"[/COLOR]")
          plot= plot_title + plot
          plot = plot.replace(plot,"[COLOR white][B]"+plot+"[/B][/COLOR]")
          plot = re.sub(r'div class=".*?">','',plot)
          plot = plot.replace("div>","")
          plot = plot.replace('div class="margin_20b">','')
          plot = plot.replace('div class="post-entry">','')
          plot = plot.replace('p style="text-align: left;">','')
          title = re.sub(r"&#.*?;","",title)
          title = title.replace(title,"[COLOR sandybrown][B]"+title+"[/B][/COLOR]")
          title = title.replace("-","")
          title = title.replace("Torrent","")
          title = title.replace("amp;","")
          title = title.replace("Descargar en Bricocine.com","")
          try:
              scrapedinfo = scrapertools.get_match(data,'Ficha técnica</h2><dl class="list"><dt>(.*?)hellip')
          except IndexError :
                 scrapedinfo = scrapertools.get_match(data,'Ficha técnica</h2><dl class="list"><dt>(.*?)</div><div class="quad-2"')
                 scrapedinfo = scrapedinfo.replace("<br />"," ")
                 scrapedinfo = scrapedinfo.replace("</dl>","<dt>")
          scrpaedinfo = re.sub(r'<a href=".*?"|title=".*?"|item.*?=".*?"','',scrapedinfo)

          infoformat = re.compile('(.*?</dt><dd.*?>).*?</dd><dt>',re.DOTALL).findall(scrapedinfo)
          for info in infoformat:
              scrapedinfo= scrapedinfo.replace(scrapedinfo,"[COLOR white][B]"+scrapedinfo+"[/COLOR]")
              scrapedinfo= scrapedinfo.replace(info,"[COLOR red][B]"+info+"[/B][/COLOR]")
          info = scrapedinfo
          info = re.sub(r'<a href=".*?">|title=".*?">|<span itemprop=.*?>|</span></span>|<span>|</a>|itemprop=".*?"|y otros.*?&','',info)
          info = info.replace("</dt><dd>",":")
          info = info.replace("</dt><dd >",":")
          info = info.replace("</dt><dd > ",":")
          info = info.replace("</dd><dt>"," ")
          info = info.replace("</span>"," ")
          
          info = info.replace("Actores:","[COLOR red][B]Actores:[/B][/COLOR] ")
          photo= item.extra
          foto = item.category
          quit = "Pulsa"+" [COLOR crimson][B]INTRO [/B][/COLOR]"+ "para quitar"
         
          NOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "noback.xml")
          REMOTENOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remotenoback.xml")
          APPNOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "appnoback.xml")
          urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/noback.xml", NOBACKDESTFILE )
          urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/remotenoback.xml", REMOTENOBACKDESTFILE)
          urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/appnoback.xml", APPNOBACKDESTFILE )
          xbmc.executebuiltin('Action(reloadkeymaps)')
    else:
        data = get_page( item.url )
        data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;","",data)
        patron = '<div class="description" itemprop="text.*?">.*?([^<]+).*?</div></div></div>.*?'
        patron += '<span class="title">([^"]+)</span>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        
        if len(matches)==0 :
            title = "[COLOR red][B]LO SENTIMOS...[/B][/COLOR]"
            plot = "Esta pelicula no tiene sinopsis..."
            plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
            foto= "http://s6.postimg.org/ub7pb76c1/noinfo.png"
            photo="http://s6.postimg.org/nm3gk1xox/noinfosup2.png"
            info =""
            quit = "Pulsa"+" [COLOR crimson][B]INTRO [/B][/COLOR]"+ "para quitar"

        for plot, title in matches:
            title = title.upper()
            title = title.replace(title,"[COLOR sandybrown][B]"+title+"[/B][/COLOR]")
            title = re.sub(r"&#.*?;","",title)
            plot_title = "Sinopsis" + "[CR]"
            plot_title = plot_title.replace(plot_title,"[COLOR red]"+plot_title+"[/COLOR]")
            plot= plot_title + plot
            plot = plot.replace(plot,"[COLOR white][B]"+plot+"[/B][/COLOR]")
            plot = plot.replace('div class="margin_20b">','')
            plot = plot.replace('div class="post-entry">','')
            try:
                scrapedinfo = scrapertools.get_match(data,'Ficha técnica</h2><dl class="list"><dt>(.*?)hellip')
            except IndexError :
                scrapedinfo = scrapertools.get_match(data,'Ficha técnica</h2><dl class="list"><dt>(.*?)</div><div class="quad-2"')
                scrapedinfo = scrapedinfo.replace("<br />"," ")
                scrapedinfo = scrapedinfo.replace("</dl>","<dt>")
            scrpaedinfo = re.sub(r'<a href=".*?"|title=".*?"|item.*?=".*?"','',scrapedinfo)
            infoformat = re.compile('(.*?</dt><dd.*?>).*?</dd><dt>',re.DOTALL).findall(scrapedinfo)
            for info in infoformat:
                scrapedinfo= scrapedinfo.replace(scrapedinfo,"[COLOR white][B]"+scrapedinfo+"[/COLOR]")
                scrapedinfo= scrapedinfo.replace(info,"[COLOR red][B]"+info+"[/B][/COLOR]")
            info = scrapedinfo
            info = re.sub(r'<a href=".*?">|title=".*?">|<span itemprop=.*?>|</span></span>|<span>|</a>|itemprop=".*?"|y otros.*?&','',info)
            info = info.replace("</dt><dd>",":")
            info = info.replace("</dt><dd >",":")
            info = info.replace("</dt><dd > ",":")
            info = info.replace("</dd><dt>"," ")
            info = info.replace("</span>"," ")
            if "hellip" in data:
               info = info.replace("Actores:","[COLOR red][B]Actores:[/B][/COLOR] ")

            foto = item.category
            photo= item.extra
            quit = "Pulsa"+" [COLOR crimson][B]INTRO [/B][/COLOR]"+ "para quitar"


    ventana2 = TextBox1(title=title, plot=plot, info= info, thumbnail=photo, fanart=foto, quit= quit)
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
                      urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/customapp.xml", APPCOMMANDDESTFILE )
                   xbmc.executebuiltin('Action(reloadkeymaps)')
               except:
                  pass
               self.close()

def test():
    return True
        


def info_capitulos(item):

    logger.info("pelisalacarta.bricocine trailer")
    import xbmc
    APPCOMMANDDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "customapp.xml")
    try:
       os.remove(APPCOMMANDDESTFILE)
    except:
       pass
    url= item.url
    data = get_page(url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    item.category = item.show.split("|")[0]
    item.thumbnail = item.show.split("|")[1]
    capitulo =item.extra.split("|")[2]
    capitulo = re.sub(r"(0)\d;","",capitulo)
    url="http://thetvdb.com/api/1D62F2F90030C444/series/"+item.show.split("|")[0]+"/default/"+item.extra.split("|")[0]+"/"+capitulo+"/es.xml"
    data = scrapertools.cache_page(url)
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
        quit = "Pulsa"+" [COLOR greenyellow][B]INTRO [/B][/COLOR]"+ "para quitar"
    else :


        for name_epi, info in matches:
            if "<filename>episodes" in data:
               foto = scrapertools.get_match(data,'<Data>.*?<filename>(.*?)</filename>')
               fanart = "http://thetvdb.com/banners/" + foto
            else:
                fanart=item.show.split("|")[1]
            
            plot = info
            plot = plot.replace(plot,"[COLOR yellow][B]"+plot+"[/B][/COLOR]")
            name_epi = re.sub(r"&#.*?;","",name_epi)
            title = name_epi.upper()
            title = title.replace(title,"[COLOR sandybrown][B]"+title+"[/B][/COLOR]")
            image=fanart
            foto= item.show.split("|")[1]
            quit = "Pulsa"+" [COLOR greenyellow][B]INTRO [/B][/COLOR]"+ "para quitar"
            NOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "noback.xml")
            REMOTENOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "remotenoback.xml")
            APPNOBACKDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "appnoback.xml")
            TESTPYDESTFILE = os.path.join(xbmc.translatePath('special://userdata/keymaps'), "test.py")
            urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/noback.xml", NOBACKDESTFILE )
            urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/remotenoback.xml", REMOTENOBACKDESTFILE)
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
                      urllib.urlretrieve ("https://raw.githubusercontent.com/neno1978/script.palc.forcerefresh/master/Bricocine/customapp.xml", APPCOMMANDDESTFILE )
                   xbmc.executebuiltin('Action(reloadkeymaps)')
               except:
                   xbmc.executebuiltin('Action(reloadkeymaps)')
               self.close()
def test():
    return True







