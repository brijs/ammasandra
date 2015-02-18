from datetime import datetime, timedelta
import os
import jwt
import json
import requests
from functools import wraps
from urlparse import parse_qs, parse_qsl
from urllib import urlencode
from flask import Flask, g, send_file, request, redirect, url_for, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from requests_oauthlib import OAuth1
from jwt import DecodeError, ExpiredSignature
from OpenSSL import SSL
import random, sys

from httplib2 import Http
from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build
import pprint


# configuration
current_path = os.path.dirname(__file__)
client_path = os.path.abspath(os.path.join(current_path, '..', 'myApp', 'www'))

app = Flask(__name__, static_url_path='', static_folder=client_path)
app.config.from_object('config')

# db
db = SQLAlchemy(app)

# ================================== DB Model ==================================
# TODO: Models can be moved out of app.py to separate file(s)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    display_name = db.Column(db.String(120))
    facebook = db.Column(db.String(120))
    github = db.Column(db.String(120))
    google = db.Column(db.String(120))
    google_access_token = db.Column(db.String(300))
    google_refresh_token = db.Column(db.String(300))
    linkedin = db.Column(db.String(120))
    twitter = db.Column(db.String(120))

    display_pic = db.Column(db.String(120))
    
    def __init__(self, email=None, password=None, display_name=None,
                 facebook=None, github=None, google=None, linkedin=None,
                 twitter=None, display_pic=None, google_access_token=None,
                 google_refresh_token=None):
        if email:
            self.email = email.lower()
        if password:
            self.set_password(password)
        if display_name:
            self.display_name = display_name
        if facebook:
            self.facebook = facebook
        if google:
            self.google = google
        if google_access_token:
            self.google_access_token = google_access_token
        if google_refresh_token:
            self.google_refresh_token = google_refresh_token
        if linkedin:
            self.linkedin = linkedin
        if twitter:
            self.twitter = twitter
        if display_pic:
            self.display_pic = display_pic

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_json(self):
        return dict(id=self.id, email=self.email, displayName=self.display_name,
                    facebook=self.facebook, google=self.google,
                    linkedin=self.linkedin, twitter=self.twitter,
                    displayPic=self.display_pic,
                    google_access_token=self.google_access_token,
                    google_refresh_token=self.google_refresh_token)


db.create_all()


# =================================== Utils ===================================
# JWT token
def create_token(user):
    payload = {
        'sub': user.id,
        'iat': datetime.now(),
        'exp': datetime.now() + timedelta(days=14)
    }
    token = jwt.encode(payload, app.config['TOKEN_SECRET'])
    return token.decode('unicode_escape')


def parse_token(req):
    # prefer token parameter over auth header (for testing)
    if req.args.get('token'):
        token = req.args.get('token')
    else:
        token = req.headers.get('Authorization').split()[1]
    
    return jwt.decode(token, app.config['TOKEN_SECRET'])



# authentication & login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (request.headers.get('Authorization') or request.args.get('token')) :
            response = jsonify(message='Missing authorization header')
            response.status_code = 401
            return response

        try:
            payload = parse_token(request)
        except DecodeError:
            response = jsonify(message='Token is invalid')
            response.status_code = 401
            return response
        except ExpiredSignature:
            response = jsonify(message='Token has expired')
            response.status_code = 401
            return response

        g.user_id = payload['sub']

        return f(*args, **kwargs)

    return decorated_function


# =========================== Google API using OAuth ===========================
def getGoogleImageSearchResults(query):
    GoogleCustomSearch = None
    
    client_email = app.config['GOOGLE_CUSTOM_SEARCH_CLIENT_ID']
    with open(app.config['GOOGLE_CUSTOM_SEARCH_PK_FILE']) as f:
        private_key = f.read()
    
    credentials = SignedJwtAssertionCredentials(client_email, private_key,
        'https://www.googleapis.com/auth/cse')

    http = Http()
    credentials.authorize(http)

    GoogleCustomSearch = build('customsearch', 'v1', http=http)
    response = GoogleCustomSearch.cse().list(q=query, 
        cx=app.config['GOOGLE_CUSTOM_SEARCH_ENGINE_ID'],
        searchType= 'image',
        imgSize="large",
        num=3,
        fields="items(image/thumbnailLink,link)").execute()
    return response


# ======================= Routes 0: client-side html/js =======================
# 
# These assets (index.html + dependent scripts, css etc) would eventually be 
# deployed as part of the client-side package (eg: apk). For now, serving
# these up from our app server.
@app.route('/')
def index():
	return send_file('../myApp/www/index.html')


# ============================= Routes 1: REST API =============================
# 
# As a convention, all "API" endpoints start with /api/<version>/...

# sau's globals: should get this from the database
currentGameId = 50
numOfQuestionsInAGame = 2
numOfOptionsPerQuestion = 3
questionSeeds = {
        'cities': [ 'mumbai', 'paris', 'new york city', 'rome', ' london' ],
        'fruits': [ 'apple', 'pear', 'grape', 'orange', 'banana', 'strawberry' ]
    }

games = {}

imageSearchURL='https://www.googleapis.com/customsearch/v1?key=AIzaSyCeiMGAnozDLIOKhSYCG5lIHbWDjRT6cVg&cx=007408032665432303252:eybewyws4ca'
    

@app.route('/api/v1/game', methods=['POST']) #brij added 'GET' to test easily from browser directly
@login_required
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
        # response = requests.get(imageSearchURL, params=queryParams)
        # probably need to add error handling here
        #print(response.text)
        # jsonResponse = json.loads( response.text )
        jsonResponse = getGoogleImageSearchResults(currentSeed)
        #print jsonResponse
        #TODO: need to scramble the link so that the answer is not obvious
        imageLink = jsonResponse['items'][0]['link']
        # print imageLink
        question = {
            'questionId': questionId,
            'questionKey': currentSeedLocation,
            'options': options,
            'imageLink': imageLink
            }
        # print question
        questions.append(question)
        
    # print questions
    # print currentGameId
    currentGameId = currentGameId + 1
    # print currentGameId
    games[currentGameId]= {}
    # print games[currentGameId]
    games[currentGameId]['questions']= questions
    user = User.query.filter_by(id=g.user_id).first()
    games[currentGameId]['userId']= user.email
    games[currentGameId]['nextQuestionId']= questions[0]['questionId']
    games[currentGameId]['score']= 0
    
    return jsonify( { 'gameID': currentGameId } ), 201


@app.route('/api/v1/game/<gameId>', methods=['GET'])
@login_required
def getGameDetails(gameId):
    # need to filter the things we don't want to send back
    return jsonify( games[int(gameId)] )


@app.route('/api/v1/game/<gameId>/questions/<questionId>', methods=['POST'])
@login_required
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
 

# @app.route('/api/v1/users/<userId>', methods=['GET'])
@app.route('/api/v1/users/me', methods=['GET'])
@login_required
def getUserDetails():
    user = User.query.filter_by(id=g.user_id).first()
    return jsonify(user.to_json())



# =========================== Routes 2: Auth related ===========================
# 
# The following endpoints implement OAuth for various providers (google,
# facebook etc). In particular, these http POSTs include a "code", 
# which is then passed along to the corresponding providers in exchange
# for "access_tokens" (& optionally "refresh_tokens"). These access_tokens
# are then used with the specific provider APIs (eg: google plus API) to
# request information (eg: profile pic) on behalf of the end-user.
@app.route('/auth/google', methods=['POST'])
def google():
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    people_api_url = 'https://www.googleapis.com/plus/v1/people/me/openIdConnect'

    payload = dict(client_id=request.json['clientId'],
                   redirect_uri=request.json['redirectUri'],
                   client_secret=app.config['GOOGLE_SECRET'],
                   code=request.json['code'],
                   grant_type='authorization_code')

    # Step 1. Exchange authorization code for access token.
    r = requests.post(access_token_url, data=payload)
    token = json.loads(r.text)
    try:
        headers = {'Authorization': 'Bearer {0}'.format(token['access_token'])}
    except KeyError:
        response = jsonify(message='Google Authentication failed: ' + token['error'])
        response.status_code = 401
        return response

    # Step 2. Retrieve information about the current user.
    r = requests.get(people_api_url, headers=headers)
    profile = json.loads(r.text)
    
    user = User.query.filter_by(google=profile['sub']).first()
    if user:
        token = create_token(user)
        return jsonify(token=token)
    u = User(google=profile['sub'],
             display_name=profile['name'],
             display_pic=profile['picture'],
             email=profile['email'],
             google_access_token=token['access_token'])
    db.session.add(u)
    db.session.commit()
    token = create_token(u)
    return jsonify(token=token)

# TODO: implement facebook
def facebook():
    response = jsonify(message='Not Implemented.')
    response.status_code = 401
    return response



# =========================== main: DEV testing only ===========================
app.debug = True
app.config['DEBUG'] = True

if __name__ == '__main__':
	# ctx = SSL.Context(SSL.SSLv23_METHOD)
	# ctx.use_privatekey_file('/home/brij/certs/ssl.key')
	# ctx.use_certificate_file('/home/brij/certs/ssl.cert')
	# app.run(host='0.0.0.0', ssl_context=ctx, port=3001)
    app.run(host='0.0.0.0', port=8000, debug=True)