# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
    #showValue:     48 Stunden
    #showEntries:    6 Stunden
    #showSeasons:    6 Stunden
    #showEpisodes:   4 Stunden
    
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'einfach'
SITE_NAME = 'Einfach'
SITE_ICON = 'einfach.png'

#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'einfach.to')
URL_MAIN = 'https://' + DOMAIN + '/'
#URL_MAIN = 'https://einfach.to/'
URL_MOVIES = URL_MAIN + 'filme/'
URL_SERIES = URL_MAIN + 'series/'
URL_KINO = URL_MAIN + 'kinofilme/'
URL_SEARCH = URL_MAIN + '?s=%s'


def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30500), SITE_IDENTIFIER, 'showEntries'), params)  # New
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  # Movies
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series
    params.setParam('sUrl', URL_KINO)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30501), SITE_IDENTIFIER, 'showEntries'), params)  # Cinema Movies
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showGenre'), params)    # Genre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))   # Search
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48 # 48 Stunden
    sHtmlContent = oRequest.request()    
    pattern = 'Genres(.*?)</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = 'href="([^"]+).*?name.*?>([^<]+)'
        isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    isTvshow = False
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + 'page/' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = '<article class="box" itemscope="itemscope".*?' # container start
    pattern += 'href="([^"]+).*?' # url
    pattern += 'lazy-src="([^"]+).*?' # thumb
    pattern += 'alt="([^"]+)".*?' # name
    pattern += '(.*?)</article>' # dummy
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        # Für die Suche von Filmen und Serien
        pattern = '<article class="box" itemscope="itemscope".*?'  # container start
        pattern += 'href="([^"]+).*?'  # url
        pattern += 'src="([^"]+).*?'  # thumb
        pattern += 'alt="([^"]+)".*?'  # name
        pattern += '(.*?)</article>'  # dummy
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        isRating, sRating = cParser.parseSingleResult(sDummy, 'IMDb:\s<b>([^<]+)</b>')  # IMDb Bewertung
        isYear, sYear = cParser.parseSingleResult(sDummy, '"addyear">([\d]+)</span>')  # Release Jahr
        isDuration, sDuration = cParser.parseSingleResult(sDummy, 'dot"></i>\s([\d]+)\smin')  # Laufzeit
        #isDesc, sDesc = cParser.parseSingleResult(sDummy, 'class="desc"><p>([^<]+)')  # Beschreibung
        isTvshow, aResult = cParser.parse(sDummy, 'class="type">TV</i>')
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        if isRating:
            oGuiElement.addItemValue('rating', sRating)
        if isYear:
            oGuiElement.setYear(sYear)
        if isDuration:
            oGuiElement.addItemValue('duration', sDuration)
        #if isDesc:
            #oGuiElement.setDescription(sDesc)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('season' if isTvshow else 'movie')
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        #params.setParam('sDesc', sDesc)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui and not sSearchText:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('page', int(sPageNr))
        params.setParam('sUrl', entryUrl)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    # Parameter laden
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    #sDesc = params.getValue('sDesc')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<div\sclass="bxtitle">(.*?)<div\sclass="homedesc">'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = 'class="ts-chl-collapsible">Staffel\s([\d]+)'
        isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    if not isMatch:
        cGui().showInfo()
        return
    total = len(aResult)
    for sSeason in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setThumbnail(sThumbnail)
        #oGuiElement.setDescription(sDesc)
        # Parameter übergeben
        params.setParam('Season', sSeason)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    # Parameter laden
    entryUrl = params.getValue('entryUrl')
    sSeason = params.getValue('Season')
    sThumbnail = params.getValue('sThumbnail')
    #sDesc = params.getValue('sDesc')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 4  # HTML Cache Zeit 4 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'collapsible">Staffel %s(.*?)</ul>' % sSeason  # Suche alles in diesem Bereich
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = '<a href="([^"]+)">.*?'  # sUrl
        pattern += 'S' + sSeason + '\sEP\s([\d]+).*?'  # Episoden Eintrag
        pattern += 'title">([^<]+)'  # sName
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch: return
    total = len(aResult)
    for sUrl, sEpisode, sName in aResult:
        oGuiElement = cGuiElement('Episode ' + sEpisode + ' - ' + sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        #oGuiElement.setDescription(sDesc)
        # Parameter übergeben
        params.setParam('Season', sSeason)
        params.setParam('Episode', sEpisode)
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    hosters = []
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<ul class="mirror">(.*?)</ul>'  # Alle Einträge in dem Bereich suchen
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'data-href="(h[^"]+).*?>([^<]+)')  # sUrl + sName
    if not isMatch: return
    for sUrl, sName in aResult:
        if 'Trailer' in sName: continue  # Trailer ausblenden
        #if cConfig().isBlockedHoster(sName)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
        hoster = {'link': sUrl, 'name': sName }
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    Request = cRequestHandler(sUrl, caching=False)
    sHtmlContent = Request.request()
    pattern = 'pembed".*?<iframe.*?src="(http[^"]+)'
    isMatch, sUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)