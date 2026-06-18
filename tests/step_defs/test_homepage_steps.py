from pytest_bdd import scenarios, when

scenarios('../features/homepage.feature')


@when('I visit the homepage', target_fixture='response')
def visit_homepage(client):
    return client.get('/')
