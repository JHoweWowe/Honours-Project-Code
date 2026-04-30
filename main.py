# Setup database for storing and retrieving food recipe data
import pymongo
from pymongo import MongoClient

client = MongoClient('localhost', 27017)

recipe_db = client['honours-proj-website-recipes']
test_recipe_collection = recipe_db['bbcgoodfood'] # By default should only collect recipes from BBCGoodFood



# Setup basic web scrapping
from bs4 import BeautifulSoup
import requests

# TODO: Web scrape multiple recipes from student recipes and obtain URL for each if applicable
test_url = 'https://www.bbcgoodfood.com/recipes/collection/student-recipes'

html_text = requests.get(test_url).text
soup = BeautifulSoup(html_text, features='html.parser') # Indicate HTML parser 
recipes = soup.findAll('li', class_ = 'dynamic-list__list-item list-item')

recipes_json_list = []

# NOTE: For BBCGoodFood, only loads information up to a certain page - should also have unique id associated to each recipe
for recipe in recipes:
    url = recipe.find('a', class_ = 'link d-block').get('href')

    title = recipe.find('h2', class_ = 'd-inline heading-4').text
    description = recipe.find('p', class_ = 'd-block body-copy-small').text # NOTE: Should it be stored???

    cooking_time = recipe.find('span', class_ = 'terms-icons-list__text d-flex align-items-center')
    cooking_difficulty = recipe.find('span', class_ = 'terms-icons-list__text d-flex align-items-center')

    # jialat how to find ingredients - from specific url can
    ingredients = None

    # TODO: Add ingredients
    recipe_json = {
        "title": title,
        "description": description
    }

    recipes_json_list.append(recipe_json)

# For debugging purposes
#print(recipes_json_list)

# Bad code practice to store and conduct bulk queries...
result = test_recipe_collection.insert_many(recipes_json_list)

