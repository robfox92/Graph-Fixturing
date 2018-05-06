# Fixturing Library, to fixture a league of arbitrary size
# Uses the NetworkX library for maximally weighted matching
import pandas as pd
import networkx as nx
import random

def getDataFromRemote(URL: str, table: str) -> pd.DataFrame:
    '''
    When passed a valid URL and a table name, will download the URL as a .xls
    and perform minimal cleaning, returning a DataFrame
    '''
    results = pd.read_excel(URL, sheetname = table).dropna(how='all')
    return results

def getResults(URL: str, table: str) -> pd.DataFrame:
    '''
    Wrapper around getDataFromRemote() for the parsing and cleaning of results-
    style data (including results and previous fixtures)
    '''
    results = getDataFromRemote(URL, table)
    results.sort_values(by='Round',inplace=True)
    return results

def getRatings(URL:str, table: str, teamNameCol: str, teamEloCol: str,
        teamKCol: str) -> (dict,dict, set):
    '''
    Wrapper around getDataFromRemote, returns a dict of the starting Elo scores
    of all the teams, a dict of their associated K values and a list of team
    names. The returned tuple is formatted (ratingsDict,kValueDict, teamNames)
    '''
    ratingsDF = getDataFromRemote(URL,table)
    # Cast the list of teams to a set to ensure we only have unique teams
    teams = set(ratingsDF[teamNameCol])
    ratingsDict = {team:ratingsDF.loc[team,teamEloCol] for team in teams}
    kValueDict = {team:ratingsDF.loc[team,teamKCol] for team in teams}
    return (ratingsDict, kValueDict, teams)

def getExpectedOutcome(eloA: float, eloB: float) -> (float, float):
    '''
    Returns the expected outcome of two Elos
    '''
    expectedOutcome = None
    if eloA == eloB:
        expectedOutcome = 0.5
    else:
        expectedOutcome = 1/(1+10**-((eloA - eloB)/400.0))
    return (expectedOutcome, 1-expectedOutcome)

def getScaledOutcome(outcome: float) -> float:
    '''
    Scales an expected outcome. Higher means a closer game
    '''
    return 2*(0.5-abs(outcome - 0.5))

def getGameOutcome(scoreA: int, scoreB: int) -> (float, float):
    '''
    Returns the scaled outcome of a match as a float. Format is
    (outcomeA, outcomeB)
    '''
    totalScore = float(scoreA + scoreB) # Cast to a float to ensure float division
    outcomeA = scoreA / totalScore      # Not required in python3 but old habits die hard
    outcomeB = scoreB / totalScore
    return (outcomeA, outcomeB)

def getDeviation(expected: float, outcome: float, elo:float, kValue: float) -> float:
    '''
    Compute the deviation of a match from the expected result, and returns the
    new Elo.
    '''
    deviation = outcome - expected
    newElo = elo + kValue * deviation
    return newElo

def updateElosFromResults(elos: dict, results: pd.DataFrame, kValues: dict) -> dict:
    '''
    Loops through the dataframe of results, and updates the Elo of each team
    Returns a dict of (updated) Elos.
    Assumes that:
        HomeTeam is kept in column "Home Team"
        AwayTeam is kept in column "Away Team"
        Home Score is kept in column "Home Score"
        Away Score is kept in column "Away Score"
    '''
    for gameRow in range(len(results)):
        # Grab data from the df
        homeTeam = results.loc[gameRow,'Home Team']
        awayTeam = results.loc[gameRow,'Away Team']
        homeK = kValues[homeTeam]
        awayK = kValues[awayTeam]
        homeElo = elos[homeTeam]
        awayElo = elos[awayTeam]
        homeScore = results.loc[gameRow,'Home Score']
        awayScore = results.loc[gameRow,'Away Score']
        
        # Start processing
        homeScorePerc, awayScorePerc = getGameOutcome(homeScore, awayScore)
        homeExpected, awayExpected = getExpectedOutcome(homeElo, awayElo) 
        homeNewElo = getDeviation(homeExpected, homeScorePerc, homeElo, homeK)
        awayNewElo = getDeviation(awayExpected, awayScorePerc, awayElo, awayK)
        
        # Ensure winning teams don't lose Elo
        if homeScore > awayScore:
            homeNewElo = max(homeElo, homeNewElo)
        if homeScore < awayScore:
            awayNewElo = max(awayElo, awayNewElo)
        
        # Create the updated Elos to push to the dict
        updatedElos = {homeTeam:homeNewElo, awayTeam: awayNewElo}
        elos.update(updatedElos)

    return elos

def checkIfGameInList(teamA: str, teamB: str, gamesList: list) -> (bool,int):
    '''
    Checks if a game is in a list. Pass it two teams and a list of games
    (requests, previous games, etc) and it will return whether or not the game
    is in the list as a bool and the count as (bool, count)
    '''
    isIn = False
    count = 0
    codeA = teamA + " vs " + teamB
    codeB = teamB + " vs " + teamB
    if codeA in gamesList:
        isIn = True
    if codeB in gamesList:
        isIn = True
    if isIn:                       # if the game is in the list, get the count
        count = gamesList.count(codeA) + gamesList.count(codeB)
    return (isIn, count)

def createGameRating(teamA: str, teamB: str, elosDict: dict, fixturedGames:
        list, requestedGames: list, antiRequestedGames: list) -> float:
    '''
    Evaluate how good a game will be, based on:
      - The teams Elos
      - Whether the game has happened before
      - Whether the game has been requested
      - Whether the game has been requested to not happen
    Returns a float indicating how good the game is. Higher is "better"
    '''
    eloA = elosDict[teamA]
    eloB = elosDict[teamB]
    # Get the expected outcome. We only use the outcome with respect to team A
    # as this should have the same scaled value as the outcome w.r.t. team B.
    # We still have the expectedOutcomeB variable available, but it is not used
    # currently.
    expectedOutcomeA, expectedOutcomeB = getExpectedOutcome(eloA, eloB)
    scaledOutcomeA = getScaledOutcome(expectedOutcomeA)
    gameFixturedPrev, gameFixturedPrevCount = checkIfGameInList(teamA, teamB, i
            fixturedGames)
    gameRequested, gameRequestedCount = checkIfGameInList(teamA, teamB,
            requestedGames)
    gameNotRequested, gameNotRequestedCount = checkIfGameInList(teamA, teamB,
            antiRequestedGames)
    gameRating = 100                           # Start with a rating of 100
    gameRating = gameRating + scaledOutcomeA   # Add by the scaledOutcome
    if gameFixturedPrev:
        gameRating = gameRating - gameFixturedPrevCount*10 # Decrement rating by
                                                    # 25*number of prev fixtures
    if gameRequested:
        gameRating = gameRating + 2
    if gameNotRequested:
        gameRating = gameRating - 4
    # Ensure we don't use negative ratings as they cause issues with maximally
    # weighted matching
    return max(gameRating,0)

def createGameRatingsGraph(teams: set, fixturedGames: list, requestedGames: list,
        antiRequests: list, elosDict: dict) -> nx.Graph():
    '''
    Creates and returns a graph (not in the chart sense) of all possible games
    between all possible teams. Each node in the graph is a team, and each edge
    in the graph represents a game between the two teams, with an edge with a
    weight representing "how good" the game will be.
    '''
    fixtureGraph = nx.Graph()
    fixtureGraph.add_nodes_from(teams)
    for teamA in teams:
        for teamB in teams:
            if teamA != teamB and not fixtureGraph.has_edge(teamA, teamB):
                edgeWeight = createGameWeighting(teamA, teamB, elosDict,
                        fixturedGames, requestedGames, antiRequestedGames)
                graph.add_edge(teamA, teamB, weight = edgeWeight)
    return fixtureGraph

def getHomeGameCounts(teams: set, fixturedGames: list) -> dict:
    '''
    Given a list of teams and a list of games, returns a dict of how many home
    games each tam has had.
    '''
    homeGameCounts = {team:0 for team in teams}
    for team in teams:
        for game in fixturedGames:
            if game.startswith(team):
                homeGameCounts[team] += 1
    return homeGameCounts

def createFixturesFromGraph(gameRatings: nx.Graph, homeGameCounts: dict) -> pd.DataFrame:
    '''
    Returns a df of fixtures, given a graph of ratings and a dict of previous home games.
    We use the homeGameCounts to try and even out the home/away split, so that all teams
    should get approximately the same number of home/away games over a season.
    '''
    bestPairings = nx.max_weight_matching(gameRatings)
    fixture = pd.DataFrame(columns=['Home Team','Away Team','Game Code'])
    row = 0
    for teamA in bestPairings.keys():
        teamB = bestPairings[teamA]
        # Check if the teams have been fixtured so far, as the dict of pairings
        # contains two entries for each "game" (e.g. {teamA:teamB,teamB:teamA}).
        # We only want to fixture each game once though.
        if (teamA not in fixture['Home Team'].unique() and
            teamB not in fixture['Home Team'].unique() and
            teamA not in fixture['Away Team'].unique() and
            teamB not in fixture['Away Team'].unique()):
            if homeGameCounts[teamA] > homeGameCounts[teamB]:
                homeTeam = teamB
                awayTeam = teamA
            else:
                homeTeam = teamA
                awayTeam = teamB
            fixture.loc[row,'Home Team'] = homeTeam
            fixture.loc[row,'Away Team'] = awayTeam
            fixture.loc[row,'Game Code'] = homeTeam + " vs " + awayTeam
            r+=1
    return fixture

def fixtureSingleRound(teams: set, elos: dict, fixtured: list, requested: list,
        antiRequested: list, rematchesAllowed = 0: int) -> pd.DataFrame:
    '''
    Fixture a single round
    '''
    complete = False
    while not complete:
        gameRatingsGraph = createGameRatingsGraph(teams, fixtured, requested, 
                antirequests, elos)
        homeGameCounts = getHomeGameCounts(teams, fixtured)
        fixtures = createFixturesFromGraph(gameRatingsGraph, fixtured, homeGameCounts)

        # Check to see if any games have been fixtured previously
        maxRepeats = 0
        for row in range(len(fixtures)):
            homeT = fixtures.loc[row,'Home Team']
            awayT = fixtures.loc[row,'Away Team']
            repeats = checkIfGameInList(homeT, awayT, fixtures)[1]
            maxRepeats = max(repeats, maxRepeats)

        if maxRepeats <= rematchesAllowed:
            complete = True
        else:
            print("Error: Could not find fixture within maxRepeats")



# TO BE IMPLEMENTED
def fixtureDoubleRound(teams: set, elos: dict, fixtured: list, requested: list,
        antiRequested: list, rematchesAllowed) -> pd.DataFrame:
    '''
    Fixture two rounds at once. This is used when there are an odd number of
    teams in the league, as we can avoid byes by fixturing two rounds at once.
    '''
    byeElo = random.choice(elos.values())
