from pytest_bdd import scenarios, when, parsers

scenarios('../features/recipe_detail.feature')


@when(parsers.parse('I view the recipe with id "{recipe_id}"'), target_fixture='response')
def view_recipe(client, recipe_id):
    return client.get(f'/recipe/{recipe_id}')
