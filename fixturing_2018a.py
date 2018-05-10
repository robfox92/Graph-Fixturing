from fixturelib_27 import *


rootURL = 'https://docs.google.com/spreadsheets/d/10RYpl2cOuze8CfiLjb1NiXsJlbWyrm-k_q33euzIdN8/export?format=xlsx&id=10RYpl2cOuze8CfiLjb1NiXsJlbWyrm-k_q33euzIdN8'
print("Enter Round Number")
roundNumber=int(input())

print("Retrieving Results from remote")
mixedResults = getResults(URL=rootURL, table='Mixed-Scores')
ladiesResults = getResults(URL=rootURL, table='Ladies-Scores')

# Grab the rating data and unpack it
ladiesRatings = getRatings(URL=rootURL, table='Ladies-Starting Elos',
        teamNameCol='TEAM NAME', teamEloCol='STARTING ELO',
        teamKCol='K Value')
mixedRatings = getRatings(URL=rootURL, table='Mixed-Starting Elos',
        teamNameCol='TEAM NAME',teamEloCol='STARTING ELO',
        teamKCol='K Value')

ladiesFixtured = list(getDataFromRemote(URL=rootURL, table='Ladies-Fixtured Games')['Game Code'])
mixedFixtured = list(getDataFromRemote(URL=rootURL, table='Mixed-Fixtured Games')['Game Code'])
mixedRequested = list(getDataFromRemote(URL=rootURL, table='Mixed-Requests')['Game Code'])
ladiesRequested = list(getDataFromRemote(URL=rootURL, table='Ladies-Requests')['Game Code'])
# Init these as empty lists
ladiesAntiRequested = list()
mixedAntiRequested = list()
print("Successfully retrieved Results from Remote")

mixedStartingElos = mixedRatings[0]
mixedKVals = mixedRatings[1]
mixedTeams = mixedRatings[2]
ladiesStartingElos = ladiesRatings[0]
ladiesKVals = ladiesRatings[1]
ladiesTeams = ladiesRatings[2]

# Process the results to update the Elos
print("Parsing results to update Ratings")
ladiesElos = updateElosFromResults(elos=ladiesStartingElos,results=ladiesResults,
        kValues=ladiesKVals)
mixedElos = updateElosFromResults(elos=mixedStartingElos,results=mixedResults,
        kValues=mixedKVals)
print("Successfully parsed results to update Ratings\nFinding Game Ratings")
# Create the Game Ratings Graph
mixedGameRatings = createGameRatingsGraph(teams=mixedTeams, fixturedGames=mixedFixtured,
        requestedGames=mixedRequested,antiRequestedGames=mixedAntiRequested,elosDict=mixedElos)
ladiesGameRatings = createGameRatingsGraph(teams=ladiesTeams, fixturedGames=ladiesFixtured,
        requestedGames=ladiesRequested,antiRequestedGames=ladiesAntiRequested,elosDict=ladiesElos)
mixedHomeGameCounts = getHomeGameCounts(mixedTeams,mixedFixtured)
ladiesHomeGameCounts = getHomeGameCounts(ladiesTeams,ladiesFixtured)
print("Successfully found Game Ratings")

mixedFixture = None
ladiesFixture = None

print("Fixturing Ladies Teams")
if len(ladiesTeams)%2 == 0:
    ladiesRoundNumber = str(roundNumber)
    ladiesFixture = fixtureSingleRound(teams=ladiesTeams, elos=ladiesElos,
            fixtured=ladiesFixtured, requested=ladiesRequested,
            antiRequested=ladiesAntiRequested,rematchesAllowed=0)
elif len(ladiesTeams)%2 == 1 and roundNumber%2 == 1:
    ladiesRoundNumber = "%i-%i" %(roundNumber,roundNumber+1)
    ladiesFixture = fixtureDoubleRound(teams=ladiesTeams, elos=ladiesElos,
            fixtured=ladiesFixtured, requested=ladiesRequested,
            antiRequested=ladiesAntiRequested,rematchesAllowed=0)

print("Ladies Fixture Complete.\nFixturing Mixed Teams")
if len(mixedTeams)%2 == 0:
    mixedRoundNumber = str(roundNumber)
    mixedFixture = fixtureSingleRound(teams=mixedTeams, elos=mixedElos,
            fixtured=mixedFixtured, requested=mixedRequested,
            antiRequested=mixedAntiRequested,rematchesAllowed=0)
elif len(mixedTeams)%2 == 1 and roundNumber%2 == 1:
    mixedRoundNumber = "%i-%i" %(roundNumber, roundNumber+1)
    mixedFixture = fixtureDoubleRound(teams=mixedTeams, elos=mixedElos,
            fixtured=mixedFixtured, requested=mixedRequested,
            antiRequested=mixedAntiRequested,rematchesAllowed=0)
print("Mixed Fixture Complete.\nWriting to CSV")
if mixedFixture is not None:
    mixedPath = "Mixed Round %s Fixtures 2018a.csv" %mixedRoundNumber
    mixedFixture.to_csv(path=mixedPath)

if ladiesFixture is not None:
    ladiesPath = "Ladies Round %s Fixtures 2018a.csv" %ladiesRoundNumber
    ladiesFixture.to_csv(path=ladiesPath)
print("Script Complete.")

