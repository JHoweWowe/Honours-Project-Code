# Setup database for storing and retrieving food recipe data
from flask_pymongo import pymongo
from web_scrapping_module_helper import WebScrapperHelper

import requests, configparser, os
from spoonacular_api import SpoonacularAPI

# Setup Configuration for API and MongoDB
spoonacular_API = SpoonacularAPI()
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

# Setup basic web scrapping
from bs4 import BeautifulSoup

base_url = 'https://www.bbcgoodfood.com/recipes/collection/student-recipes'
page_number_str = config.get('web_scrapping_module', 'page')
url_query = '?' + 'page=' + page_number_str
url = base_url + url_query

html_text = requests.get(url).text
soup = BeautifulSoup(html_text, features='html.parser') # Indicate HTML parser 
recipes = soup.findAll('li', class_ = 'dynamic-list__list-item list-item')

recipes_json_list = []

web_scrapper_helper = WebScrapperHelper()

# NOTE: For BBCGoodFood, only loads information up to a certain page - should also have unique id associated to each recipe
for recipe in recipes:
    specific_recipe_url = recipe.find('a', class_ = 'link d-block').get('href')

    title = recipe.find('h2', class_ = 'd-inline heading-4').text
    description = recipe.find('p', class_ = 'card__description d-block body-copy-small').text
    
    image_url = recipe.find('img', class_ = 'image__img')['src']

    # jialat specifically find information from individual recipe url can
    individual_recipe_url = base_url + specific_recipe_url
    individual_html_recipe_text = requests.get(individual_recipe_url).text
    soup = BeautifulSoup(individual_html_recipe_text, features='html.parser')

    # Obtain author - for credability
    author_div = soup.find('div', class_='author-link')
    author_str = author_div.find('a', class_='link link--styled').get_text()

    # Obtain total time
    total_cooking_time_div = soup.find('div', class_ = 'icon-with-text time-range-list cook-and-prep-time post-header__cook-and-prep-time')
    prep_and_cook_time_list = total_cooking_time_div.find_all('time')

    total_cooking_time = 0

    for i in prep_and_cook_time_list:
        if i.has_attr('datetime'):
            total_cooking_time += WebScrapperHelper().convert_timeStr_to_Mins(i.text)

    # Obtain default servings
    some_ul = soup.find('ul', class_='post-header__row post-header__planning list list--horizontal')
    default_servings_ul = some_ul.find('li', class_='mt-sm list-item')
    default_servings_text = default_servings_ul.get_text()
    try:
        default_servings = int(default_servings_text.split(" ")[1])
    except ValueError:
        default_servings = 0

    # Obtain rating details - including average rating and number of ratings
    rating_details = soup.find('div', class_='rating__values').find_all('span', limit=2) # Only obtain average rating & num of ratings
    average_rating_str = rating_details[0].get_text()
    average_rating = float(average_rating_str.split(" ")[4]) # Eg: 'A star rating of 4.5 out of 5.'

    number_of_ratings_str = rating_details[1].get_text()
    number_of_ratings = int(number_of_ratings_str.split(" ")[0])

    # Obtain nutrition details
    nutrition_per_serving_details_table = soup.find('table', class_='key-value-blocks hidden-print mt-xxs')
    table1_contents = nutrition_per_serving_details_table.contents[2]
    table2_contents = nutrition_per_serving_details_table.contents[3]
    nutrition_per_serving_details = dict()
    for content in table1_contents:
        key = content.contents[0].get_text()
        value = content.contents[1].get_text()
        nutrition_per_serving_details[key] = value
    for content in table2_contents:
        key = content.contents[0].get_text()
        value = content.contents[1].get_text()
        nutrition_per_serving_details[key] = value

    # Obtain dietary requirements
    dietary_requirements_ul = soup.find('ul', class_='terms-icons-list d-flex post-header__term-icons-list mt-sm hidden-print list list--horizontal')
    dietary_requirements_array = []
    allowed_dietary_requirements_array = ['Vegan', 'Vegetarian', 'Gluten-free'] # To be refactored more to allow more dq options
    if dietary_requirements_ul is not None:
        for t in dietary_requirements_ul:
            if t.span.get_text() in allowed_dietary_requirements_array:
                dietary_requirements_array.append(t.span.get_text())

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
        steps_array.append(str(t2.p.text) + ' ')

    # Classify cuisine
    main_cuisine = spoonacular_API.classify_cuisine(api_key, title, list_of_ingredients_array)

    # Analyze recipe instructions (aka get equipment)
    steps_str = ''.join(steps_array)
    ingredients_tag_list, equipment_list = spoonacular_API.analyze_recipe_instructions(api_key, steps_str)

    # TODO: Add prep, cook & total time and 
    recipe_json = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "total_time": total_cooking_time,
        "author": author_str,
        "default_servings": default_servings,
        "dietary_requirements": dietary_requirements_array,
        "nutrition_per_servings": nutrition_per_serving_details,
        "average_rating": average_rating,
        "number_of_ratings": number_of_ratings,
        "ingredients": list_of_ingredients_array,
        "ingredient_tags": ingredients_tag_list,
        "steps": steps_array,
        "equipment": equipment_list,
        "cuisine": main_cuisine
    }

    recipes_json_list.append(recipe_json)

#print(recipes_json_list) # For debugging purposes

# Bad code practice to store individual recipes...better to conduct bulk queries for faster time runtime
result = test_recipe_collection.insert_many(recipes_json_list)

