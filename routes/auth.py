import os
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, redirect, url_for, current_app, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_login import login_user, logout_user, current_user

from extensions import login_manager

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Google OAuth blueprint — credentials read from env at import time (after load_dotenv).
# Register this at url_prefix='/auth/google' so the callback lands at /auth/google/authorized.
# Add that URL to Google Cloud Console → OAuth 2.0 → Authorised redirect URIs.
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID', ''),
    client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', ''),
    scope=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
)


class User:
    def __init__(self, doc):
        self.id = str(doc['_id'])
        self.google_id = doc.get('google_id', '')
        self.email = doc.get('email', '')
        self.display_name = doc.get('display_name', '')
        self.postcode = doc.get('postcode', '')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


@login_manager.user_loader
def load_user(user_id):
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    doc = current_app.mongo.db.users.find_one({'_id': oid})
    return User(doc) if doc else None


@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        return False
    resp = blueprint.session.get('/oauth2/v2/userinfo')
    if not resp.ok:
        return False
    info = resp.json()
    google_id = str(info.get('id', ''))
    email = info.get('email', '')
    display_name = info.get('name') or email.split('@')[0]

    mongo = current_app.mongo
    user_doc = mongo.db.users.find_one({'google_id': google_id})
    if user_doc is None:
        result = mongo.db.users.insert_one({
            'google_id': google_id,
            'email': email,
            'display_name': display_name,
            'created_at': datetime.now(timezone.utc),
        })
        user_doc = {
            '_id': result.inserted_id,
            'google_id': google_id,
            'email': email,
            'display_name': display_name,
        }

    login_user(User(user_doc), remember=True)
    return False  # prevent Flask-Dance from storing the token in its session


@bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return redirect(url_for('google.login'))


@bp.route('/logout')
def logout():
    session.clear()   # clear Flask-Dance token before logout_user sets _remember='clear'
    logout_user()
    return redirect(url_for('main.index'))
