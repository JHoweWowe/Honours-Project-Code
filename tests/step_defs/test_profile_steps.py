from pytest_bdd import scenarios, given, when

scenarios('../features/profile.feature')

_VALID_FORM = {
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


@given('I am logged in as a test user', target_fixture='logged_in_client')
def logged_in(logged_in_client):
    return logged_in_client


@when('I visit the profile page without logging in', target_fixture='response')
def visit_profile_unauthenticated(client):
    return client.get('/profile/', follow_redirects=False)


@when('I visit the profile page', target_fixture='response')
def visit_profile(logged_in_client):
    return logged_in_client.get('/profile/')


@when('I submit the profile form without a first name', target_fixture='response')
def submit_no_first_name(logged_in_client):
    data = {**_VALID_FORM, 'first_name': ''}
    return logged_in_client.post('/profile/', data=data, follow_redirects=True)


@when('I submit a valid profile form', target_fixture='response')
def submit_valid_form(logged_in_client):
    return logged_in_client.post('/profile/', data=_VALID_FORM, follow_redirects=True)


@when('I submit the profile form with an invalid date of birth', target_fixture='response')
def submit_invalid_dob(logged_in_client):
    data = {**_VALID_FORM, 'dob': 'not-a-date'}
    return logged_in_client.post('/profile/', data=data, follow_redirects=True)


@when('I submit the profile form with zero budget', target_fixture='response')
def submit_zero_budget(logged_in_client):
    data = {**_VALID_FORM, 'max_budget_gbp': '0'}
    return logged_in_client.post('/profile/', data=data, follow_redirects=True)


@when('I submit the profile form with household size out of range', target_fixture='response')
def submit_bad_household(logged_in_client):
    data = {**_VALID_FORM, 'household_size': '25'}
    return logged_in_client.post('/profile/', data=data, follow_redirects=True)
