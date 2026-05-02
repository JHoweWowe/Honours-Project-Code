from pytest_bdd import scenarios, given, when

scenarios('../features/auth.feature')


@when('I visit the homepage', target_fixture='response')
def visit_homepage(client):
    return client.get('/')


@given('I am logged in as a test user', target_fixture='logged_in_client')
def logged_in(logged_in_client):
    return logged_in_client


@given('I am logged in with remember me enabled', target_fixture='logged_in_client')
def logged_in_remember(logged_in_client_with_remember):
    return logged_in_client_with_remember


@when('I visit the homepage as a logged in user', target_fixture='response')
def visit_homepage_logged_in(logged_in_client):
    return logged_in_client.get('/')


@when('I sign out', target_fixture='response')
def sign_out(logged_in_client):
    return logged_in_client.get('/auth/logout', follow_redirects=True)


@when('I visit the login page while authenticated', target_fixture='response')
def visit_login_authenticated(logged_in_client):
    return logged_in_client.get('/auth/login', follow_redirects=False)
