import urllib.parse as urlparse
from datetime import datetime
from decimal import Decimal
from os import makedirs, path

from pydash import replace_end

from fetchESPN import fetch

SEASON_ID = datetime.now().year

def parseQueryString( queryStr:str ):
    return urlparse.parse_qs(urlparse.urlparse(queryStr).query)

def getLeagueInfo():
    scheduleSoup = fetch.fetchSchedule(SEASON_ID)
    leagueName = replace_end(scheduleSoup.title.text,' Schedule -  ESPN', '')
    print( "Beginning parse of %s's %s season..." % (leagueName, SEASON_ID) )

    schedule = dict()
    teamInfo = dict()
    links = scheduleSoup.find('table', class_='tableBody').find_all('a', href=True)
    for a in links:
        url = a['href']
        if 'boxscorequick' in url:
            query_def = parseQueryString(url)
            teamId = query_def['teamId'][0]
            scoringPeriodId = query_def['scoringPeriodId'][0]
            if scoringPeriodId not in schedule:
                schedule[scoringPeriodId] = []
            schedule[scoringPeriodId].append(teamId)
        elif 'clubhouse' in url:
            query_def = parseQueryString(url)
            teamId = query_def['teamId'][0]
            if teamId not in teamInfo:
                teamInfo[teamId] = a.text
    return schedule, leagueName, teamInfo

def getScoreInfo( scoreSoup ):
    d = dict()
    currentIndex = 0
    totalScores = scoreSoup.find_all('div', class_='totalScore')
    benchScores = scoreSoup.select('div[id*="tmInactivePts"]')
    teamNames = scoreSoup.find('div', id='teamInfos').find_all('a')
    for team in teamNames:
        teamId = parseQueryString(team['href'])['teamId'][0]
        d[teamId] = dict()
        actualPoints = Decimal(totalScores[currentIndex]['title'])
        benchPoints = Decimal(benchScores[currentIndex].text if len(benchScores) > 0 else 0)
        d[teamId]['actual'] = float(actualPoints)
        d[teamId]['bench'] = float(benchPoints)
        d[teamId]['total'] = float(actualPoints + benchPoints)
        currentIndex += 1
    return d

def parseLeagueResults( weeks:dict ):
    leagueResults = dict()
    for week in weeks:
        print('Parsing week %s...' % (week), end='', flush=True)
        leagueResults[week] = []
        for teamId in weeks[week]:
            scoreboardText = fetch.fetchScoreboard(teamId, week, SEASON_ID)
            scoreInfo = getScoreInfo(scoreboardText)
            leagueResults[week].append(scoreInfo)
        print('DONE')
        break
    return leagueResults

def printResults( leagueName:str, leagueResults:dict ):
    resultDirectory = 'results'
    outputFileName = ('%s/%s-%s.txt' % (resultDirectory, leagueName.replace(' ', '-'), SEASON_ID))
    print('Printing to %s...' % (outputFileName), end='', flush=True)
    if not path.exists(resultDirectory):
        makedirs(resultDirectory)
    print(leagueResults, file=open(outputFileName, 'w'))
    print('DONE')

def main():
    scheduleInfo, leagueName, teamInfo = getLeagueInfo()
    leagueResults = parseLeagueResults(scheduleInfo)
    printResults(leagueName, leagueResults)

main()
