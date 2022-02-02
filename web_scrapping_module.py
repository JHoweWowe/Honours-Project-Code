# Setup database for storing and retrieving food recipe data
from pymongo import MongoClient

from web_scrapping_module_helper import WebScrapperHelper

client = MongoClient('localhost', 27017)
recipe_db = client['honours-proj-website-recipes']
test_recipe_collection = recipe_db['bbcgoodfood'] # By default should only collect recipes from BBCGoodFood

# Setup API
import requests, configparser, os
from spoonacular_api import SpoonacularAPI

spoonacular_API = SpoonacularAPI()
config = configparser.ConfigParser()
# Handle Settings initialization file
if not os.path.exists('settings.ini'):
    config['api_keys'] = {'spoonacular_api_key': 'write_your_api_key_here'}
    config.write(open('settings.ini', 'w'))
else:
    config.read('settings.ini')

api_key = config.get('api_keys', 'spoonacular_api_key')


# Setup basic web scrapping
from bs4 import BeautifulSoup

# TODO: Web scrape multiple recipes from student recipes and obtain URL for each if applicable
base_url = 'https://www.bbcgoodfood.com/recipes/collection/student-recipes'

html_text = requests.get(base_url).text
soup = BeautifulSoup(html_text, features='html.parser') # Indicate HTML parser 
recipes = soup.findAll('li', class_ = 'dynamic-list__list-item list-item')

recipes_json_list = []

web_scrapper_helper = WebScrapperHelper()

# NOTE: For BBCGoodFood, only loads information up to a certain page - should also have unique id associated to each recipe
for recipe in recipes:
    specific_recipe_url = recipe.find('a', class_ = 'link d-block').get('href')

    title = recipe.find('h2', class_ = 'd-inline heading-4').text
    description = recipe.find('p', class_ = 'd-block body-copy-small').text
    
    image_url = recipe.find('img', class_ = 'image__img')['src']

    total_time_str = recipe.find('span', class_ = 'terms-icons-list__text d-flex align-items-center').text
    total_time_mins = web_scrapper_helper.convert_timeStr_to_Mins(total_time_str)

    #cooking_difficulty = recipe.find('span', class_ = 'terms-icons-list__text d-flex align-items-center')

    # jialat specifically find information from individual recipe url can
    individual_recipe_url = base_url + specific_recipe_url
    individual_html_recipe_text = requests.get(individual_recipe_url).text
    soup = BeautifulSoup(individual_html_recipe_text, features='html.parser')

    # Obtain rating details - including average rating and number of ratings
    rating_details = soup.find('div', class_='rating__values').find_all('span', limit=2) # Only obtain average rating & num of ratings
    average_rating_str = rating_details[0].get_text()
    average_rating = float(average_rating_str.split(" ")[4]) # Eg: 'A star rating of 4.5 out of 5.'

    number_of_ratings_str = rating_details[1].get_text()
    number_of_ratings = int(number_of_ratings_str.split(" ")[0])

    # Obtain dietary requirements
    dietary_requirements_ul = soup.find('ul', class_='terms-icons-list d-flex post-header__term-icons-list mt-sm hidden-print list list--horizontal')
    dietary_requirements_array = []
    if dietary_requirements_ul is not None:
        for t in dietary_requirements_ul:
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

    # Analyze recipe instructions (aka get equipment)
    steps_str = ''.join(steps_array)
    equipment_list = spoonacular_API.analyze_recipe_instructions(api_key, steps_str)

    # TODO: Add prep, cook & total time and 
    recipe_json = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "total_time": total_time_mins,
        "dietary_requirements": dietary_requirements_array,
        "average_rating": average_rating,
        "number_of_ratings": number_of_ratings,
        "ingredients": list_of_ingredients_array,
        "steps": steps_array,
        "equipment": equipment_list
    }

    recipes_json_list.append(recipe_json)

#print(recipes_json_list) # For debugging purposes

# Bad code practice to store individual recipes...better to conduct bulk queries for faster time runtime
result = test_recipe_collection.insert_many(recipes_json_list)

