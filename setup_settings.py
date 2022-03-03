# Setup config settings

import configparser, os
config = configparser.ConfigParser()

if not os.path.exists('settings.ini'):
    config['api_keys'] = {'spoonacular_api_key': ''}
    config['food_recipe_database'] = {
        'food_recipe_database_name': 'db',
        'food_collection_name': 'bbc_good_food',
        'username': 's1840358',
        'password': ''
    }
    config.write(open('settings.ini', 'w'))