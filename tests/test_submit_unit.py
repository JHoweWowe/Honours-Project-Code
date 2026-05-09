"""Unit tests for routes/submit.py — submission, admin, and my-submissions flows."""
import pytest
from bson import ObjectId
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_pending(app, user_id=None):
    """Insert a pending user recipe and return its ObjectId."""
    from datetime import datetime, timezone
    oid = ObjectId()
    app.mongo.db.user_recipes.insert_one({
        '_id': oid,
        'title': 'Test Community Pie',
        'ingredients': ['100g flour', '50g butter'],
        'steps': ['Mix flour and butter', 'Bake at 180C'],
        'cuisine': 'British',
        'dietary_requirements': [],
        'total_time': 40,
        'image_url': None,
        'servings': 4,
        'submitted_by': user_id or ObjectId('507f1f77bcf86cd799439099'),
        'submitted_at': datetime.now(timezone.utc),
        'status': 'pending',
        'moderation_note': None,
        'source': 'user',
    })
    return oid


# ---------------------------------------------------------------------------
# Unauthenticated access — all submit routes require login
# ---------------------------------------------------------------------------

def test_submit_form_redirects_when_not_logged_in(client):
    resp = client.get('/submit-recipe')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_admin_recipes_redirects_when_not_logged_in(client):
    resp = client.get('/admin/recipes')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_my_submissions_redirects_when_not_logged_in(client):
    resp = client.get('/my-submissions')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


# ---------------------------------------------------------------------------
# Submit form — GET
# ---------------------------------------------------------------------------

def test_submit_form_renders_for_logged_in_user(app, logged_in_client):
    resp = logged_in_client.get('/submit-recipe')
    assert resp.status_code == 200
    assert b'Submit a Recipe' in resp.data


# ---------------------------------------------------------------------------
# Submit recipe — POST validation
# ---------------------------------------------------------------------------

def test_submit_missing_title_shows_error(app, logged_in_client):
    resp = logged_in_client.post('/submit-recipe', data={
        'title': '',
        'ingredients': '100g flour',
        'steps': 'Mix and bake',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'title is required' in resp.data.lower()


def test_submit_title_too_long_shows_error(app, logged_in_client):
    resp = logged_in_client.post('/submit-recipe', data={
        'title': 'A' * 101,
        'ingredients': '100g flour',
        'steps': 'Mix and bake',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'100 characters' in resp.data.lower()


def test_submit_missing_ingredients_shows_error(app, logged_in_client):
    resp = logged_in_client.post('/submit-recipe', data={
        'title': 'My Recipe',
        'ingredients': '',
        'steps': 'Mix and bake',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'ingredients are required' in resp.data.lower()


def test_submit_missing_steps_shows_error(app, logged_in_client):
    resp = logged_in_client.post('/submit-recipe', data={
        'title': 'My Recipe',
        'ingredients': '100g flour',
        'steps': '',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'steps are required' in resp.data.lower()


def test_valid_submission_inserts_pending_recipe(app, logged_in_client):
    before = app.mongo.db.user_recipes.count_documents({'title': 'Grandma Soup'})
    resp = logged_in_client.post('/submit-recipe', data={
        'title': 'Grandma Soup',
        'ingredients': '2 carrots\n1 onion\n500ml stock',
        'steps': 'Chop vegetables\nSimmer for 30 mins',
        'cuisine': 'British',
        'total_time': '35',
        'servings': '4',
    }, follow_redirects=True)
    assert resp.status_code == 200
    after = app.mongo.db.user_recipes.count_documents({'title': 'Grandma Soup'})
    assert after == before + 1
    doc = app.mongo.db.user_recipes.find_one({'title': 'Grandma Soup'})
    assert doc['status'] == 'pending'
    assert doc['source'] == 'user'
    assert doc['ingredients'] == ['2 carrots', '1 onion', '500ml stock']
    assert doc['steps'] == ['Chop vegetables', 'Simmer for 30 mins']
    assert doc['total_time'] == 35


def test_admin_submission_auto_approves(app, logged_in_client):
    app.config['ADMIN_EMAILS'] = ['testuser@example.com']
    resp = logged_in_client.post('/submit-recipe', data={
        'title': 'Admin Instant Soup',
        'ingredients': '1 onion\n500ml stock',
        'steps': 'Simmer and serve',
    }, follow_redirects=True)
    assert resp.status_code == 200
    doc = app.mongo.db.user_recipes.find_one({'title': 'Admin Instant Soup'})
    assert doc is not None
    assert doc['status'] == 'approved'
    app.config['ADMIN_EMAILS'] = ['howejust@gmail.com']


def test_valid_submission_with_dietary_tags(app, logged_in_client):
    logged_in_client.post('/submit-recipe', data={
        'title': 'Vegan Tacos',
        'ingredients': '6 corn tortillas\n1 cup black beans',
        'steps': 'Warm tortillas\nFill with beans',
        'dietary_tags': ['Vegan', 'Vegetarian'],
    }, follow_redirects=True)
    doc = app.mongo.db.user_recipes.find_one({'title': 'Vegan Tacos'})
    assert doc is not None
    assert 'Vegan' in doc['dietary_requirements']
    assert 'Vegetarian' in doc['dietary_requirements']


# ---------------------------------------------------------------------------
# Admin — access control
# ---------------------------------------------------------------------------

def test_admin_recipes_forbidden_for_non_admin(app, logged_in_client):
    resp = logged_in_client.get('/admin/recipes')
    assert resp.status_code == 403


def test_admin_recipes_accessible_for_admin(app, logged_in_client):
    with app.test_request_context('/'):
        app.config['ADMIN_EMAILS'] = ['testuser@example.com']
    resp = logged_in_client.get('/admin/recipes')
    assert resp.status_code == 200
    assert b'Recipe Review' in resp.data
    app.config['ADMIN_EMAILS'] = ['howejust@gmail.com']


# ---------------------------------------------------------------------------
# Admin — approve and reject
# ---------------------------------------------------------------------------

def test_approve_recipe_sets_status(app, logged_in_client):
    app.config['ADMIN_EMAILS'] = ['testuser@example.com']
    oid = _insert_pending(app)
    resp = logged_in_client.post(f'/admin/recipes/{oid}/approve', follow_redirects=True)
    assert resp.status_code == 200
    doc = app.mongo.db.user_recipes.find_one({'_id': oid})
    assert doc['status'] == 'approved'
    app.config['ADMIN_EMAILS'] = ['howejust@gmail.com']


def test_reject_recipe_sets_status_and_note(app, logged_in_client):
    app.config['ADMIN_EMAILS'] = ['testuser@example.com']
    oid = _insert_pending(app)
    resp = logged_in_client.post(
        f'/admin/recipes/{oid}/reject',
        data={'moderation_note': 'Ingredients list is incomplete.'},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    doc = app.mongo.db.user_recipes.find_one({'_id': oid})
    assert doc['status'] == 'rejected'
    assert doc['moderation_note'] == 'Ingredients list is incomplete.'
    app.config['ADMIN_EMAILS'] = ['howejust@gmail.com']


def test_reject_recipe_without_note(app, logged_in_client):
    app.config['ADMIN_EMAILS'] = ['testuser@example.com']
    oid = _insert_pending(app)
    resp = logged_in_client.post(
        f'/admin/recipes/{oid}/reject',
        data={'moderation_note': ''},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    doc = app.mongo.db.user_recipes.find_one({'_id': oid})
    assert doc['status'] == 'rejected'
    assert doc['moderation_note'] is None
    app.config['ADMIN_EMAILS'] = ['howejust@gmail.com']


def test_approve_invalid_id_returns_400(app, logged_in_client):
    app.config['ADMIN_EMAILS'] = ['testuser@example.com']
    resp = logged_in_client.post('/admin/recipes/not-an-objectid/approve')
    assert resp.status_code == 400
    app.config['ADMIN_EMAILS'] = ['howejust@gmail.com']


# ---------------------------------------------------------------------------
# My submissions
# ---------------------------------------------------------------------------

def test_my_submissions_returns_200(app, logged_in_client):
    resp = logged_in_client.get('/my-submissions')
    assert resp.status_code == 200
    assert b'My Submissions' in resp.data


def test_my_submissions_shows_empty_state_when_no_submissions(app, logged_in_client):
    app.mongo.db.user_recipes.delete_many({'submitted_by': ObjectId('507f1f77bcf86cd799439099')})
    resp = logged_in_client.get('/my-submissions')
    assert resp.status_code == 200
    assert b"haven't submitted" in resp.data.lower()


def test_my_submissions_shows_user_recipes(app, logged_in_client):
    user_oid = ObjectId('507f1f77bcf86cd799439099')
    oid = _insert_pending(app, user_id=user_oid)
    resp = logged_in_client.get('/my-submissions')
    assert resp.status_code == 200
    assert b'Test Community Pie' in resp.data
    app.mongo.db.user_recipes.delete_one({'_id': oid})
