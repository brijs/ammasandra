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

# configuration
current_path = os.path.dirname(__file__)
client_path = os.path.abspath(os.path.join(current_path, '..', 'myApp', 'www'))

app = Flask(__name__, static_url_path='', static_folder=client_path)
app.config.from_object('config')

# db
db = SQLAlchemy(app)

# db Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    display_name = db.Column(db.String(120))
    facebook = db.Column(db.String(120))
    github = db.Column(db.String(120))
    google = db.Column(db.String(120))
    linkedin = db.Column(db.String(120))
    twitter = db.Column(db.String(120))

    display_pic = db.Column(db.String(120))
    
    def __init__(self, email=None, password=None, display_name=None,
                 facebook=None, github=None, google=None, linkedin=None,
                 twitter=None, display_pic=None):
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
                    displayPic=self.display_pic)

db.create_all()


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
	if req.headers.get('Authorization'):
		token = req.headers.get('Authorization').split()[1]
	else:
		token = req.args.get('token')

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



# Routes (client-side html/js)

@app.route('/')
def index():
	return send_file('../myApp/www/index.html')


# Routes (REST API)

@app.route('/api/users/me')
@login_required
def me():
    user = User.query.filter_by(id=g.user_id).first()
    return jsonify(user.to_json())


# Routes (auth)

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
    headers = {'Authorization': 'Bearer {0}'.format(token['access_token'])}

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
             email=profile['email'])
    db.session.add(u)
    db.session.commit()
    token = create_token(u)
    return jsonify(token=token)


if __name__ == '__main__':
	# ctx = SSL.Context(SSL.SSLv23_METHOD)
	# ctx.use_privatekey_file('/home/brij/certs/ssl.key')
	# ctx.use_certificate_file('/home/brij/certs/ssl.cert')
	# app.run(host='0.0.0.0', ssl_context=ctx, port=3001)
    app.run(host='0.0.0.0', port=3001)