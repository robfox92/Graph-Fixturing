# Fixturing Library, to fixture a league of arbitrary size
# Uses the NetworkX library for maximally weighted matching
import pandas as pd


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
