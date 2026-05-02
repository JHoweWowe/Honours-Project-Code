import sys
import pytest
import mongomock
from unittest.mock import patch
from bson import ObjectId
from pytest_bdd import given, then, parsers

# ---------------------------------------------------------------------------
# Seed documents — inserted once per session into the in-memory mongomock db.
# Three BBC recipes and one Tasty recipe cover every filter / relation tested.
# ---------------------------------------------------------------------------

_BBC_RECIPE_1 = {
    '_id': ObjectId('507f1f77bcf86cd799439011'),
    'title': 'Simple Pasta Bolognese',
    'description': 'A classic Italian pasta dish for students',
    'image_url': '',
    'total_time': 30,
    'author': 'Test Author',
    'default_servings': 4,
    'average_rating': 4.7,
    'number_of_ratings': 200,
    'dietary_requirements': [],
    'nutrition_per_servings': {'kcal': '450kcal'},
    'ingredients': ['200g spaghetti', '1 onion'],
    'ingredient_tags': ['spaghetti', 'onion'],
    'steps': ['Boil pasta for 10 mins', 'Cook the sauce', 'Combine and serve'],
    'equipment': ['pan', 'pot'],
    'cuisine': 'Italian',
    'prices': [
        {'currency': 'USD', 'overall_cost_per_serving': 2.50, 'overall_cost': 10.00,
         'ingredients_name_cost_list': {'spaghetti': 0.50}},
        {'currency': 'GBP', 'overall_cost_per_serving': 1.80, 'overall_cost': 7.20,
         'ingredients_name_cost_list': {'spaghetti': 0.40}},
    ],
}

_BBC_RECIPE_2 = {
    '_id': ObjectId('507f1f77bcf86cd799439012'),
    'title': 'Vegan Buddha Bowl',
    'description': 'A healthy vegan bowl packed with plant protein',
    'image_url': '',
    'total_time': 20,
    'author': 'Test Author 2',
    'default_servings': 2,
    'average_rating': 4.5,
    'number_of_ratings': 150,
    'dietary_requirements': ['Vegan', 'Vegetarian'],
    'nutrition_per_servings': {'kcal': '300kcal'},
    'ingredients': ['1 cup chickpeas', '1 avocado'],
    'ingredient_tags': ['chickpeas', 'avocado'],
    'steps': ['Prepare all ingredients', 'Assemble the bowl'],
    'equipment': ['bowl'],
    'cuisine': 'American',
    'prices': [
        {'currency': 'USD', 'overall_cost_per_serving': 3.00, 'overall_cost': 6.00,
         'ingredients_name_cost_list': {'chickpeas': 0.50}},
        {'currency': 'GBP', 'overall_cost_per_serving': 2.20, 'overall_cost': 4.40,
         'ingredients_name_cost_list': {'chickpeas': 0.40}},
    ],
}

_BBC_RECIPE_3 = {
    '_id': ObjectId('507f1f77bcf86cd799439013'),
    'title': 'Quick Stir Fry',
    'description': 'A quick and easy noodle stir fry',
    'image_url': '',
    'total_time': 15,
    'author': 'Test Author 3',
    'default_servings': 2,
    'average_rating': 4.6,
    'number_of_ratings': 100,
    'dietary_requirements': [],
    'nutrition_per_servings': {},
    'ingredients': ['200g noodles', '1 pepper'],
    'ingredient_tags': ['noodles', 'pepper'],
    'steps': ['Heat wok over high heat', 'Stir fry everything for 5 mins'],
    'equipment': ['wok'],
    'cuisine': 'Chinese',
    'prices': [
        {'currency': 'USD', 'overall_cost_per_serving': 1.50, 'overall_cost': 3.00,
         'ingredients_name_cost_list': {'noodles': 0.80}},
        {'currency': 'GBP', 'overall_cost_per_serving': 1.20, 'overall_cost': 2.40,
         'ingredients_name_cost_list': {'noodles': 0.60}},
    ],
}

_TEST_USER = {
    '_id': ObjectId('507f1f77bcf86cd799439099'),
    'google_id': 'test_google_id_123',
    'email': 'testuser@example.com',
    'display_name': 'Test User',
}

_TASTY_RECIPE_1 = {
    '_id': ObjectId('507f1f77bcf86cd799439021'),
    'title': 'Italian Pizza Margherita',
    'description': 'Classic Italian pizza with fresh basil and mozzarella',
    'image_url': '',
    'total_time': 45,
    'author': 'Tasty',
    'default_servings': 4,
    'average_rating': 0,
    'number_of_ratings': 0,
    'dietary_requirements': ['Vegetarian'],
    'nutrition_per_servings': {},
    'ingredients': ['pizza dough', 'tomato sauce', 'mozzarella'],
    'ingredient_tags': ['dough', 'tomato', 'mozzarella'],
    'steps': ['Prepare the dough', 'Add toppings', 'Bake at 220C for 15 mins'],
    'equipment': ['oven', 'baking tray'],
    'cuisine': 'Italian',
    'prices': [
        {'currency': 'USD', 'overall_cost_per_serving': 2.00, 'overall_cost': 8.00,
         'ingredients_name_cost_list': {'dough': 1.00}},
        {'currency': 'GBP', 'overall_cost_per_serving': 1.50, 'overall_cost': 6.00,
         'ingredients_name_cost_list': {'dough': 0.80}},
    ],
}

# ---------------------------------------------------------------------------
# App fixture — session-scoped so the in-memory db is shared across all tests.
# MongoClient is patched before main.py is imported so the module-level
# app = create_app() call uses mongomock instead of the real PyMongo driver.
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    sys.modules.pop('main', None)
    with patch('pymongo.MongoClient', mongomock.MongoClient):
        import main as _main
        application = _main.app
        application.config['TESTING'] = True

        db = application.mongo.db
        db.bbcgoodfood.insert_many([_BBC_RECIPE_1, _BBC_RECIPE_2, _BBC_RECIPE_3])
        db.tasty.insert_many([_TASTY_RECIPE_1])
        db.users.insert_one(_TEST_USER)

        yield application

        db.bbcgoodfood.drop()
        db.tasty.drop()
        db.users.drop()


# ---------------------------------------------------------------------------
# Auth helper fixture — simulates a logged-in user via Flask-Login session.
# ---------------------------------------------------------------------------

@pytest.fixture
def logged_in_client(app, client):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(_TEST_USER['_id'])
        sess['_fresh'] = True
    return client


@pytest.fixture
def logged_in_client_with_remember(app, client):
    # Set _remember='set' so Flask-Login's after_request places the remember_token cookie.
    with client.session_transaction() as sess:
        sess['_user_id'] = str(_TEST_USER['_id'])
        sess['_fresh'] = True
        sess['_remember'] = 'set'
    # A real request is required to trigger the after_request handler that sets the cookie.
    client.get('/')
    return client


# ---------------------------------------------------------------------------
# Shared BDD step definitions — used across all feature files.
# ---------------------------------------------------------------------------

@given('the database is seeded with test recipes')
def database_seeded():
    pass  # seeding is done once in the session-scoped app fixture above


@then(parsers.parse('the response status is {code:d}'))
def check_response_status(response, code):
    assert response.status_code == code


@then(parsers.parse('the page contains "{text}"'))
def page_contains_text(response, text):
    assert text.lower() in response.data.decode('utf-8').lower()


@then(parsers.parse('the page does not contain "{text}"'))
def page_does_not_contain_text(response, text):
    assert text.lower() not in response.data.decode('utf-8').lower()
