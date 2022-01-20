# Test Configuration of Server
import pymongo
from pymongo import MongoClient
client = MongoClient('localhost', 27017)

recipe_db = client['honours-proj-website-recipes']
test_recipe_collection = recipe_db['bbcgoodfood'] # By default should only collect recipes from BBCGoodFood

recipe = {"title": "Mom's Spaghetti",
        "description": "Test!",
        "tags": ["meow", "python", "pymongo"]}

test_recipe_collection.insert_one(recipe)