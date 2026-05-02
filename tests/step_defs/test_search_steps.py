from pytest_bdd import scenarios, when, parsers

scenarios('../features/search.feature')


@when('I search with no filters', target_fixture='response')
def search_no_filters(client):
    return client.get('/search')


@when(parsers.parse('I search with cuisine filter "{cuisine}"'), target_fixture='response')
def search_by_cuisine(client, cuisine):
    return client.get(f'/search?cuisine={cuisine}')


@when(parsers.parse('I search with dietary filter "{dq}"'), target_fixture='response')
def search_by_dietary(client, dq):
    return client.get(f'/search?dq={dq}')


@when(parsers.parse('I search with maximum time {time:d}'), target_fixture='response')
def search_by_time(client, time):
    return client.get(f'/search?time={time}')


@when(parsers.parse('I search sorted by "{sort}"'), target_fixture='response')
def search_sorted(client, sort):
    return client.get(f'/search?sort={sort}')
