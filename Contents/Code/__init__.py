# -*- coding: utf-8 -*
import re

Login = SharedCodeService.sfkidslib.Login
MakeVideoObject = SharedCodeService.sfkidslib.MakeVideoObject

BASE_URL = "https://pp.sfkids.com"

VIDEO_PREFIX = "/video/sfkids"

ART = 'art-default.jpg'
ICON = 'icon-default.jpg'
ICON_PREFS = 'icon-prefs.png'

IPAD_UA = 'Mozilla/5.0 (iPad; CPU OS 5_1 like Mac OS X; en-us) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B176 Safari/7534.48.3'

####################################################################################################

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.
def Start():
    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
    Plugin.AddViewGroup('List', viewMode = 'List', mediaType = 'items')
    
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = L('Title')
    ObjectContainer.view_group = 'List'
    
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = IPAD_UA

# This main function will setup the displayed items.
@handler(VIDEO_PREFIX, L('Title'), ICON)
def MainMenu():
    oc = ObjectContainer()
    try:
        Login()
        oc.add(CreateDirObject("Movies", Callback(Movies, title2="Movies", url=MakeUrl("Movies"))))
        oc.add(CreateDirObject("TV Shows", Callback(Series, title2="TV Shows", url=MakeUrl("Series"))))
        oc.add(CreateDirObject("Re-Login", Callback(ReLogin)))
        oc.add(PrefsObject(title = L('Preferences Menu Title'), thumb=R(ICON_PREFS)))
        oc.add(InputDirectoryObject(key    = Callback(Search), 
                                    title  = "Search", 
                                    prompt = "Search",
                                    thumb  = R('icon-search.png')
                                    )
               )
    except:
        oc.add(CreateDirObject("Login (failed)", Callback(MainMenu)))
        oc.add(PrefsObject(title = L('Preferences Menu Title'), thumb = R(ICON_PREFS)))

    return oc

@route('/video/sfkids/movies')
def Movies(title2, url):
    Log("JTDEBUG Movies(%s %s)" % (title2, url))
    oc = ObjectContainer(title2=unicode(title2))

    for item in JSON.ObjectFromURL(url)['Items']:
        if item['SortTitle'] != "":
            oc.add(MakeVideoObject(item))

    oc.objects.sort(key=lambda obj: obj.title)
    return oc

@route('/video/sfkids/series')
def Series(title2, url):
    Log("JTDEBUG Series(%s %s)" % (title2, url))
    oc = ObjectContainer(title2=unicode(title2))

    for item in JSON.ObjectFromURL(url)['Items']:
        if item['SortTitle'] != "n/a":
            oc.add(MakeTvShowObject(item))

    oc.objects.sort(key=lambda obj: obj.title)
    return oc

def Search (query):
    Log("JTDEBUG Search (%s)" % query)
    oc = ObjectContainer(title2='Search')
    unquotedQuery = query
    query = String.Quote(query)
    for hit in JSON.ObjectFromURL(MakeUrl("Medias") + '&search=' + query)['Items']:
        oc.add(MakeVideoObject(hit))

    if len(oc) == 0:
        return MessageContainer(
            "Search results",
            "Did not find any result for '%s'" % unquotedQuery
            )

    return oc

@route('/video/sfkids/show')
def Show(title2, url):
    Log("JTDEBUG Show(%s %s)" % (title2, url))
    oc = ObjectContainer(title2=unicode(title2))

    for season in JSON.ObjectFromURL(url):
        if len(season['Episodes']) == 0:
            continue

        title = "Season %s" % season['SeasonNo']
        url = BASE_URL + re.sub("([?&][^=]+={[^}]+})+", "?take=500", season['AllEpisodes']['Href'])
        
        oc.add(SeasonObject(
                key           = Callback(Season, title2=title, url=url, show=title2),
                rating_key    = url,
                index         = season['SeasonNo'],
                title         = title,
                show          = title2,
                episode_count = len(season['Episodes']),
                thumb         = GetThumb(season, 1),
                )
               )
    if len(oc) == 1:
        return Season(title, url, title2)

    oc.objects.sort(key=lambda obj: obj.index, reverse=True)
    return oc

@route('/video/sfkids/season')
def Season(title2, url, show):
    Log("JTDEBUG Season(%s %s %s)" % (title2, url, show))
    oc = ObjectContainer(title2=unicode(title2))

    for item in JSON.ObjectFromURL(url)['Items']:
        oc.add(MakeVideoObject(item, show))

    oc.objects.sort(key=lambda obj: obj.index)
    return oc

@route('/video/sfkids/relogin', 'GET')
def ReLogin():
    Login(True)
    return MainMenu()

def MakeUrl(Item):
    return BASE_URL + "/Neonstingray.Nettv4.RestApi/api/se/23/%s?language=%s&take=500" % (Item, Prefs['language'])

def GetThumb(item, type_id):
    thumb = R(ICON)
    for image in item['Images']:
        if image['TypeId'] == type_id:
            thumb = image['Link']['Href']
            break;
    return thumb

def MakeTvShowObject(item):
    title = item['SortTitle']
    url = BASE_URL + item['Seasons']['Href']
    return TVShowObject(key            = Callback(Show, title2=title, url=url),
                        rating_key     = url,
                        title          = title,
                        thumb          = GetThumb(item, 1),
                        summary        = unicode(item['LongSummary'])
                        )

def CreateDirObject(name, key, thumb=R(ICON), art=R(ART), summary=None):
    myDir         = DirectoryObject()
    myDir.title   = name
    myDir.key     = key
    myDir.summary = summary
    myDir.thumb   = thumb
    myDir.art     = art
    return myDir
