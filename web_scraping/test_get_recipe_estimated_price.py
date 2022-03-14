from spoonacular_api import SpoonacularAPI
import configparser

config = configparser.ConfigParser()
config.read('settings.ini')

api_key = config.get('api_keys', 'spoonacular_api_key')

test_ingredients_list = [
    '½ small pack coriander, roughly chopped',
    '600g baby aubergines, sliced into rounds',
    '3 tbsp olive oil',
    '2 onions, finely sliced',
    '2 garlic cloves, crushed',
    '1 tsp garam masala',
    '1 tsp turmeric',
    '1 tsp ground coriander',
    '400ml can chopped tomatoes',
    '400ml can coconut milk',
    'pinch of sugar (optional)',
    'rice or chapatis, to serve',
]

SpoonacularAPI().get_recipe_estimated_price(
    api_key=api_key,
    ingredients_list=test_ingredients_list,
    servings=4,
)