# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
# showGenre:     48 Stunden
# showEntries:    6 Stunden
# showSeasons:    6 Stunden
# showEpisodes:   4 Stunden


from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'streampalace'
SITE_NAME = 'StreamPalace'
SITE_ICON = 'streampalace.png'

# Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'streampalace.org')
URL_MAIN = 'https://' + DOMAIN + '/'
# URL_MAIN = 'https://streampalace.org/'
URL_MOVIES = URL_MAIN + 'filme/'
URL_SERIES = URL_MAIN + 'serien/'
URL_SEARCH = URL_MAIN + '?s=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  # Movies
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showGenre'), params)  # Genre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30508), SITE_IDENTIFIER, 'showYears'), params)  # Jahre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))  # Search
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<ul class="genres.*?</ul>'  # Alle Einträge in dem Bereich suchen
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')  # sUrl + sName
    if not isMatch: return
    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showYears():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<ul class="releases falsescroll">.*?</ul>'  # Alle Einträge in dem Bereich suchen
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')  # sUrl + sName
        if not isMatch: return
    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    isTvshow = False
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=sGui is not False)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<div id="archive-content".*?</article>\</div>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        # Für Filme und Serien Content
        pattern = '<article id=".*?'  # container start
        pattern += 'src="([^"]+).*?'  # sThumbnail
        pattern += 'href="([^"]+).*?'  # url
        pattern += '>([^<]+).*?'  # name
        pattern += '(.*?)</article>'  # dummy
        isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    if not isMatch:
        # Für die Suche von Filmen und Serien
        pattern = '<article.*?'  # container start
        pattern += '<img src="([^"]+).*?'  # sThumbnail alt
        pattern += 'href="([^"]+).*?'  # url
        pattern += '>([^<]+).*?'  # name
        pattern += '(.*?)</article>'  # dummy
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    total = len(aResult)
    for sThumbnail, sUrl, sName, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName): continue
        isTvshow, aResult = cParser.parse(sUrl, 'serien')  # Muss nur im Serien Content auffindbar sein
        isDesc, sDesc = cParser.parseSingleResult(sDummy, '<div class="texto">([^<]+)')  # Beschreibung
        if not isDesc:
            isDesc, sDesc = cParser.parseSingleResult(sDummy, 'class="contenido"><p>([^<]+)\s')  # Beschreibung in der Suche
        isYear, sYear = cParser.parseSingleResult(sDummy, 'class="imdb">\S+.*?\S+.*?<span>([\d]+)')  # Release Jahr
        if not isYear:
            isYear, sYear = cParser.parseSingleResult(sDummy, 'class="year">([\d]+)')  # Release Jahr in der Suche
        if not isYear:
            isYear, sYear = cParser.parseSingleResult(sDummy, 'metadata"> <span>([\d]+)')  # Release Jahr

        isDuration, sDuration = cParser.parseSingleResult(sDummy, '<span>([\d]+)\smin')  # Laufzeit
        isRating, sRating = cParser.parseSingleResult(sDummy, 'IMDb:([^<]+)')  # IMDb Bewertung
        if not isRating:
            isRating, sRating = cParser.parseSingleResult(sDummy, 'IMDb\s([^<]+)')  # IMDb Bewertung in der Suche
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if isYear:
            oGuiElement.setYear(sYear)
        if isTvshow is False:  # Laufzeit bei Serie ausblenden
            if isDuration:
                oGuiElement.addItemValue('duration', sDuration)
        if isRating:
            oGuiElement.addItemValue('rating', sRating)
        # Parameter übergeben
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sDesc', sDesc)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui and not sSearchText:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<link[^>]*rel="next"[^>]*href="([^"]+)"')  # Nächste Seite
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    # Parameter laden
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sDesc = params.getValue('sDesc')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    isMatch, aResult = cParser.parse(sHtmlContent, 'Staffel ([\d]+)')  # Sucht den Staffel Eintrag und d fügt die Anzahl hinzu
    if not isMatch: return
    total = len(aResult)
    for sSeason in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc)
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
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 4  # HTML Cache Zeit 4 Stunden
    sHtmlContent = oRequest.request()
    pattern = '>Staffel %s <i>.*?</ul>' % sSeason  # Suche alles in diesem Bereich
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = "mark-([\d]+).*?"  # Episoden Eintrag
        pattern += "img src='([^']+).*?"  # sThumbnail
        pattern += "<a href='([^']+).*?"  # sUrl
        pattern += ">([^<]+)</a>"  # sName
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        pattern = 'mark-([\d]+).*?'  # Episoden Eintrag
        pattern += 'img src="([^"]+).*?'  # sThumbnail
        pattern += '<a href="([^"]+).*?'  # sUrl
        pattern += '>([^<]+)</a>'  # sName
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch: return
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'class="wp-content">(.*?)</p>')  # Beschreibung
    total = len(aResult)
    for sEpisode, sThumbnail, sUrl, sName in aResult:
        oGuiElement = cGuiElement('Episode ' + sEpisode + ' - ' + sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        # Parameter übergeben
        params.setParam('sName', sName)
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<tbody>.*?</tbody>'  # Alle Einträge in dem Bereich suchen
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, "href='([^']+).*?>([^<]+)")  # sUrl + sName
    if not isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')  # sUrl + sName
    if not isMatch: return
    sQuality = '720p'
    for sUrl, sName in aResult:
        if cConfig().isBlockedHoster(sName)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
        hoster = {'link': sUrl, 'name': sName, 'displayedName': '%s [I][%s][/I]' % (sName, sQuality), 'quality': sQuality, 'resolveable': True}
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    Request = cRequestHandler(sUrl, caching=False)
    Request.request()
    sUrl = Request.getRealUrl()  # hole reale sURL
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)