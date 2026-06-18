"""Unit tests for routes/auth.py — User class, load_user, and google_logged_in handler."""
import pytest
from unittest.mock import MagicMock, patch
from bson import ObjectId


# ---------------------------------------------------------------------------
# User class
# ---------------------------------------------------------------------------

def test_user_is_active(app):
    from routes.auth import User
    user = User({'_id': ObjectId(), 'google_id': 'g', 'email': 'e@x.com', 'display_name': 'N'})
    assert user.is_active is True


def test_user_is_anonymous(app):
    from routes.auth import User
    user = User({'_id': ObjectId(), 'google_id': 'g', 'email': 'e@x.com', 'display_name': 'N'})
    assert user.is_anonymous is False


def test_user_get_id(app):
    from routes.auth import User
    oid = ObjectId()
    user = User({'_id': oid, 'google_id': 'g', 'email': 'e@x.com', 'display_name': 'N'})
    assert user.get_id() == str(oid)


# ---------------------------------------------------------------------------
# load_user
# ---------------------------------------------------------------------------

def test_load_user_invalid_objectid(app):
    from routes.auth import load_user
    with app.test_request_context('/'):
        result = load_user('not-a-valid-objectid')
    assert result is None


def test_load_user_nonexistent_id(app):
    from routes.auth import load_user
    with app.test_request_context('/'):
        result = load_user(str(ObjectId()))  # valid format but not in DB
    assert result is None


# ---------------------------------------------------------------------------
# google_logged_in signal handler
# ---------------------------------------------------------------------------

def test_google_logged_in_no_token(app):
    from routes.auth import google_logged_in, google_bp
    with app.test_request_context('/'):
        result = google_logged_in(google_bp, None)
    assert result is False


def test_google_logged_in_failed_response(app):
    from routes.auth import google_logged_in
    mock_bp = MagicMock()
    mock_bp.session.get.return_value.ok = False
    with app.test_request_context('/'):
        result = google_logged_in(mock_bp, {'access_token': 'tok'})
    assert result is False


def test_google_logged_in_creates_new_user(app):
    from routes.auth import google_logged_in
    mock_bp = MagicMock()
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        'id': 'brand_new_google_id',
        'email': 'brand_new@example.com',
        'name': 'Brand New',
    }
    mock_bp.session.get.return_value = mock_resp
    with app.test_request_context('/'):
        with patch('routes.auth.login_user'):
            result = google_logged_in(mock_bp, {'access_token': 'tok'})
    assert result is False
    user_doc = app.mongo.db.users.find_one({'google_id': 'brand_new_google_id'})
    assert user_doc is not None
    assert user_doc['email'] == 'brand_new@example.com'


def test_google_logged_in_existing_user(app):
    from routes.auth import google_logged_in
    mock_bp = MagicMock()
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        'id': 'test_google_id_123',  # already in DB (seeded in conftest)
        'email': 'testuser@example.com',
        'name': 'Test User',
    }
    mock_bp.session.get.return_value = mock_resp
    with app.test_request_context('/'):
        with patch('routes.auth.login_user'):
            result = google_logged_in(mock_bp, {'access_token': 'tok'})
    assert result is False
