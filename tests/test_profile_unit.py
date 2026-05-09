"""Unit tests for routes/profile.py — GET/POST /profile/"""
from datetime import datetime, timezone

from bson import ObjectId

_USER_ID = '507f1f77bcf86cd799439099'


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _post(client, data, follow=True):
    return client.post('/profile/', data=data, follow_redirects=follow)


def _valid_data(**overrides):
    base = {
        'first_name': 'Alice',
        'dob': '1995-06-15',
        'household_size': '2',
        'max_budget_gbp': '12.50',
        'skill_level': 'intermediate',
        'cooking_frequency': 'often',
        'dietary_prefs': ['Vegetarian'],
        'preferred_cuisines': ['Italian'],
        'location': 'United Kingdom',
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# GET /profile/
# ---------------------------------------------------------------------------

class TestProfileView:
    def test_redirects_unauthenticated_user(self, client):
        resp = client.get('/profile/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_returns_200_for_authenticated_user(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        assert resp.status_code == 200

    def test_page_contains_profile_heading(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        assert b'My Profile' in resp.data

    def test_page_shows_user_email(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        assert b'testuser@example.com' in resp.data

    def test_first_name_input_is_rendered(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        assert b'name="first_name"' in resp.data

    def test_page_contains_all_four_sections(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        body = resp.data.decode('utf-8').lower()
        assert 'about you' in body
        assert 'cooking preferences' in body
        assert 'dietary preferences' in body
        assert 'preferred cuisines' in body

    def test_page_contains_dietary_checkboxes(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        body = resp.data.decode('utf-8')
        for option in ['Vegetarian', 'Vegan', 'Gluten-Free', 'Pescatarian']:
            assert option in body

    def test_page_contains_skill_level_options(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        body = resp.data.decode('utf-8').lower()
        for level in ['beginner', 'intermediate', 'advanced']:
            assert level in body

    def test_page_contains_cooking_frequency_options(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        body = resp.data.decode('utf-8').lower()
        for freq in ['rarely', 'sometimes', 'often', 'daily']:
            assert freq in body

    def test_page_contains_location_input(self, logged_in_client):
        resp = logged_in_client.get('/profile/')
        assert b'name="location"' in resp.data

    def test_saved_values_prepopulate_on_revisit(self, app, logged_in_client):
        _post(logged_in_client, _valid_data())
        resp = logged_in_client.get('/profile/')
        body = resp.data.decode('utf-8')
        assert 'Alice' in body
        assert 'United Kingdom' in body

    def test_saved_dob_renders_as_date_string(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(dob='1990-03-22'))
        resp = logged_in_client.get('/profile/')
        assert b'1990-03-22' in resp.data


# ---------------------------------------------------------------------------
# POST /profile/ — validation
# ---------------------------------------------------------------------------

class TestProfileUpdateValidation:
    def test_missing_first_name_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(first_name=''))
        assert b'First name is required' in resp.data

    def test_whitespace_only_first_name_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(first_name='   '))
        assert b'First name is required' in resp.data

    def test_invalid_dob_format_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(dob='not-a-date'))
        assert b'Date of birth must be a valid date' in resp.data

    def test_zero_budget_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(max_budget_gbp='0'))
        assert b'Max budget must be greater than 0' in resp.data

    def test_negative_budget_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(max_budget_gbp='-5'))
        assert b'Max budget must be greater than 0' in resp.data

    def test_non_numeric_budget_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(max_budget_gbp='abc'))
        assert b'Max budget must be a number' in resp.data

    def test_household_size_zero_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(household_size='0'))
        assert b'Household size must be between 1 and 20' in resp.data

    def test_household_size_above_max_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(household_size='21'))
        assert b'Household size must be between 1 and 20' in resp.data

    def test_non_integer_household_size_flashes_error(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(household_size='two'))
        assert b'Household size must be a whole number' in resp.data

    def test_validation_error_does_not_save_to_db(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(first_name=''))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc.get('first_name') != ''


# ---------------------------------------------------------------------------
# POST /profile/ — successful save
# ---------------------------------------------------------------------------

class TestProfileUpdateSuccess:
    def test_success_flashes_saved_message(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data())
        assert b'Profile saved!' in resp.data

    def test_success_redirects_to_profile_get(self, logged_in_client):
        resp = _post(logged_in_client, _valid_data(), follow=False)
        assert resp.status_code == 302
        assert '/profile/' in resp.headers['Location']

    def test_first_name_saved_to_db(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(first_name='Bob'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['first_name'] == 'Bob'

    def test_display_name_synced_to_first_name(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(first_name='Carol'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['display_name'] == 'Carol'

    def test_dob_saved_as_datetime(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(dob='1992-08-10'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert isinstance(doc['dob'], datetime)
        assert doc['dob'].year == 1992
        assert doc['dob'].month == 8
        assert doc['dob'].day == 10

    def test_max_budget_saved_as_float(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(max_budget_gbp='8.50'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['max_budget_gbp'] == 8.50

    def test_household_size_saved_as_int(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(household_size='3'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['household_size'] == 3

    def test_skill_level_saved(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(skill_level='advanced'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['skill_level'] == 'advanced'

    def test_invalid_skill_level_not_saved(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(skill_level='expert'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc.get('skill_level') != 'expert'

    def test_cooking_frequency_saved(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(cooking_frequency='daily'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['cooking_frequency'] == 'daily'

    def test_invalid_cooking_frequency_not_saved(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(cooking_frequency='every tuesday'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc.get('cooking_frequency') != 'every tuesday'

    def test_dietary_prefs_saved_as_list(self, app, logged_in_client):
        _post(logged_in_client, {**_valid_data(), 'dietary_prefs': ['Vegan', 'Gluten-Free']})
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert set(doc['dietary_prefs']) == {'Vegan', 'Gluten-Free'}

    def test_invalid_dietary_pref_silently_dropped(self, app, logged_in_client):
        _post(logged_in_client, {**_valid_data(), 'dietary_prefs': ['Vegetarian', 'Carnivore']})
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert 'Carnivore' not in doc['dietary_prefs']
        assert 'Vegetarian' in doc['dietary_prefs']

    def test_preferred_cuisines_saved_as_list(self, app, logged_in_client):
        _post(logged_in_client, {**_valid_data(), 'preferred_cuisines': ['Italian', 'Chinese']})
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert set(doc['preferred_cuisines']) == {'Italian', 'Chinese'}

    def test_location_saved(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(location='Scotland'))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['location'] == 'Scotland'

    def test_empty_location_saved_as_empty_string(self, app, logged_in_client):
        _post(logged_in_client, _valid_data(location=''))
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc['location'] == ''

    def test_profile_updated_at_is_set(self, app, logged_in_client):
        _post(logged_in_client, _valid_data())
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert isinstance(doc.get('profile_updated_at'), datetime)

    def test_empty_optional_fields_not_overwritten_with_empty(self, app, logged_in_client):
        # Empty string for an invalid enum value must not store '' in the DB.
        # skill_level and cooking_frequency are silently cleared when value is invalid/empty.
        _post(logged_in_client, {'first_name': 'Dave', 'skill_level': '', 'cooking_frequency': ''})
        doc = app.mongo.db.users.find_one({'_id': ObjectId(_USER_ID)})
        assert doc.get('skill_level') != ''
        assert doc.get('cooking_frequency') != ''

    def test_unauthenticated_post_redirects_to_login(self, client):
        resp = _post(client, _valid_data(), follow=False)
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']
