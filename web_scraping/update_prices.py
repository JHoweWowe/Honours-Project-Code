from flask_pymongo import pymongo
import configparser
from spoonacular_api import SpoonacularAPI

# Setup Configuration for PyMongo
config = configparser.ConfigParser()
config.read('settings.ini')

base_uri = 'mongodb+srv://'

db_name_str = config.get('food_recipe_database', 'food_recipe_database_name')
test_recipe_collection_str = config.get('food_recipe_database', 'food_collection_name')

username = config.get('food_recipe_database', 'username')
password = config.get('food_recipe_database', 'password')
uri = base_uri + username + ':' + password + '@honours-project.x6odc.mongodb.net/db?retryWrites=true&w=majority'

mongo_client = pymongo.MongoClient(uri)
recipe_db = mongo_client[db_name_str]
test_recipe_collection = recipe_db[test_recipe_collection_str]

api_key = config.get('api_keys', 'spoonacular_api_key')

# Find all BBCGoodFood documents
bbcgoodfood_documents = mongo_client.db.bbcgoodfood.find()

# iterate over the Cursor obj for documents
for doc in bbcgoodfood_documents[0:]:

    # Obtain ingredients list and number of servings
    ingredients_list = doc['ingredients']
    number_of_servings = doc['default_servings']

    # Obtain estimated recipe prices - in forms of USD and GBP
    recipe_price_obj_list = SpoonacularAPI().get_recipe_estimated_price(api_key, ingredients_list, number_of_servings)

    mongo_client.db.bbcgoodfood.update_one({"_id": doc["_id"]}, {"$set": {"prices": recipe_price_obj_list}})

