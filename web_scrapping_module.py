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
base_url = 'https://www.bbcgoodfood.com/recipes/collection/student-recipes'

html_text = requests.get(base_url).text
soup = BeautifulSoup(html_text, features='html.parser') # Indicate HTML parser 
recipes = soup.findAll('li', class_ = 'dynamic-list__list-item list-item')

recipes_json_list = []

# NOTE: For BBCGoodFood, only loads information up to a certain page - should also have unique id associated to each recipe
for recipe in recipes:
    specific_recipe_url = recipe.find('a', class_ = 'link d-block').get('href')

    title = recipe.find('h2', class_ = 'd-inline heading-4').text
    description = recipe.find('p', class_ = 'd-block body-copy-small').text # NOTE: Should it be stored???
    
    image_url = recipe.find('img', class_ = 'image__img')['src']

    cooking_time = recipe.find('span', class_ = 'terms-icons-list__text d-flex align-items-center').text
    cooking_difficulty = recipe.find('span', class_ = 'terms-icons-list__text d-flex align-items-center')


    # jialat specifically find information from individual recipe url can
    individual_recipe_url = base_url + specific_recipe_url
    individual_html_recipe_text = requests.get(individual_recipe_url).text
    soup = BeautifulSoup(individual_html_recipe_text, features='html.parser')
    individual_recipe_itself = soup.find('div', class_='post recipe')
    ingredients = individual_recipe_itself.find('div', class_ = 'row recipe__instructions')

    # Obtain ingredients
    list_of_ingredients_array = []
    test = ingredients.find('ul', class_='list')
    for t in test:
        list_of_ingredients_array.append(t.text)

    # Obtain steps
    steps_array = []
    test2 = ingredients.find('ul', class_='grouped-list__list list')
    for t2 in test2:
        steps_array.append(t2.p.text)


    # TODO: Add ingredients
    recipe_json = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "time": cooking_time,
        "ingredients": list_of_ingredients_array,
        "steps": steps_array
    }

    recipes_json_list.append(recipe_json)

#print(recipes_json_list) # For debugging purposes

# Bad code practice to store and conduct bulk queries...
result = test_recipe_collection.insert_many(recipes_json_list)

