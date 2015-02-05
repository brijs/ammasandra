from flask import Flask, url_for, jsonify, request
import random, requests, sys, json
app = Flask(__name__)

# should get this from the database
currentGameId = 50
numOfQuestionsInAGame = 2
numOfOptionsPerQuestion = 3
questionSeeds = {
        'cities': [ 'mumbai', 'paris', 'new york city', 'rome', ' london' ],
        'fruits': [ 'apple', 'pear', 'grape', 'orange', 'banana', 'strawberry' ]
    }

games = {}

imageSearchURL='https://www.googleapis.com/customsearch/v1?key=AIzaSyCeiMGAnozDLIOKhSYCG5lIHbWDjRT6cVg&cx=007408032665432303252:eybewyws4ca'
    
@app.route('/', methods=['GET'])
def displayRootMessage():
    return 'Welcome to Ammasandra'

@app.route('/game', methods=['POST'])
def createGame():
    #if not request.json:
    #    abort(400)
    # need to change randint to sample and have an iteration for each seed
    global currentGameId
    global games
    questions = []
    currentSeedLocations = random.sample(range(0,len(questionSeeds['cities'])-1),numOfQuestionsInAGame)
    print currentSeedLocations
    print currentGameId
    for questionId in range(0, len(currentSeedLocations)):
        print questionId
        currentSeedLocation = currentSeedLocations[questionId]
        currentSeed = questionSeeds['cities'][currentSeedLocation]
        allOptions = questionSeeds['cities'][:]
        allOptions.remove(currentSeed)
        options = random.sample( allOptions, numOfOptionsPerQuestion )
        options.append(currentSeed)
        random.shuffle(options)
        print(options)
        queryParams = {
            'q': currentSeed,
            'searchType': 'image'
            }
        response = requests.get(imageSearchURL, params=queryParams)
        # probably need to add error handling here
        #print(response.text)
        jsonResponse = json.loads( response.text )
        #print jsonResponse
        #TODO: need to scramble the link so that the answer is not obvious
        imageLink = jsonResponse['items'][0]['link']
        print imageLink
        question = {
            'questionId': questionId,
            'questionKey': currentSeedLocation,
            'options': options,
            'imageLink': imageLink
            }
        print question
        questions.append(question)
        
    print questions
    print currentGameId
    currentGameId = currentGameId + 1
    print currentGameId
    games[currentGameId]= {}
    print games[currentGameId]
    games[currentGameId]['questions']= questions
    games[currentGameId]['userId']= 'sau'
    games[currentGameId]['nextQuestionId']= questions[0]['questionId']
    games[currentGameId]['score']= 0
    
    return jsonify( { 'gameID': currentGameId } ), 201

@app.route('/game/<gameId>', methods=['GET'])
def getGameDetails(gameId):
    # need to filter the things we don't want to send back
    return jsonify( games[int(gameId)] )

@app.route('/game/<gameId>/questions/<questionId>', methods=['POST'])
def checkAnswer(gameId, questionId):
    print 'check answer for gameId: ' + gameId + ' and questionId: ' + questionId
    print request
    if not request.json or not 'answer' in request.json:
        abort(400)
    # validate that the questionid is the expected next questionid
    if ( int(questionId) != games[int(gameId)]['nextQuestionId']) or ( int(questionId) == -1 ):
        print 'invalid questionId. Expected: ' + games[int(gameId)]['nextQuestionId'] + ' but got ' + questionId
        abort(400)
    if ( request.json['answer'] == questionSeeds['cities'][games[int(gameId)]['questions'][int(questionId)]['questionKey']] ):
        print 'correct answer ' + request.json['answer']
        games[int(gameId)]['score'] += 100
        if ( games[int(gameId)]['nextQuestionId'] < (numOfQuestionsInAGame -1) ):
            games[int(gameId)]['nextQuestionId'] += 1
        else:
            games[int(gameId)]['nextQuestionId']= -1
        response = True
    else:
        print games[int(gameId)]['questions'][int(questionId)]['questionKey']
        print games[int(gameId)]['questions'][int(questionId)]
        print questionSeeds['cities']
        print 'correct answer was ' + questionSeeds['cities'][games[int(gameId)]['questions'][int(questionId)]['questionKey']]+ '. Submitted answer was ' + request.json['answer'] 
        response = False

    return jsonify( { 'result': response } ), 201    
            
@app.route('/users/<userId>', methods=['GET'])
def getUserDetails(userId):
    return 'Details for user: ' + userId

if __name__ == '__main__':
    app.run()
