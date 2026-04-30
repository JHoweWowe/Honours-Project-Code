# Setup config settings

import configparser, os
config = configparser.ConfigParser()

if not os.path.exists('settings.ini'):
    config['api_keys'] = {'spoonacular_api_key': ''}
    config['food_recipe_database'] = {
        'food_recipe_database_name': 'db',
        'food_collection_name': 'foodrecipewebsite',
        'username': '',
        'password': '',
        'hostname': 'somemongodb-cluster.randomid.mongodb.net'
    }
    config['web_scrapping_module'] = {
        'base_url': 'https://www.bbcgoodfood.com/recipes/collection/student-recipes',
        'page': '1',
        'q': 'quick'
    }
    config.write(open('settings.ini', 'w'))