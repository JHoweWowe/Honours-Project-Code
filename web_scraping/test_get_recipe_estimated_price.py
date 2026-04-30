# NOTE: TO BE DELETED

from spoonacular_api import SpoonacularAPI
import configparser

config = configparser.ConfigParser()
config.read('settings.ini')

api_key = config.get('api_keys', 'spoonacular_api_key')

test_ingredients_list = [
    '½ small pack coriander, roughly chopped',
    '1 salmon fillet',
    '½ cup walnuts (50 g), chopped',
    '¼ cup lemon juice (60 mL), + 3 tablespoons',
    '½ cup olive oil (120 mL), + 2 tablespoons',
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