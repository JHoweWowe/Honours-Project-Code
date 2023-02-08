# Setup database for storing and retrieving food recipe data
from flask_pymongo import pymongo
from web_scrapping_module_helper import WebScrapperHelper

import configparser, time
from spoonacular_api import SpoonacularAPI

# Setup Configuration for PyMongo
config = configparser.ConfigParser()
config.read('settings.ini')

base_uri = 'mongodb+srv://'

db_name_str = config.get('food_recipe_database', 'food_recipe_database_name')
test_recipe_collection_str = config.get('food_recipe_database', 'food_collection_name')

username = config.get('food_recipe_database', 'username')
password = config.get('food_recipe_database', 'password')
hostname = config.get('food_recipe_database', 'hostname')
uri = base_uri + username + ':' + password + '@' + hostname + '/db?retryWrites=true&w=majority'

mongo_client = pymongo.MongoClient(uri)
recipe_db = mongo_client[db_name_str]
test_recipe_collection = recipe_db[test_recipe_collection_str]

api_key = config.get('api_keys', 'spoonacular_api_key')

# Setup basic web scrapping
from bs4 import BeautifulSoup
from selenium import webdriver # Required for obtaining image HTML, additionally used for future cross-browser testing
#from selenium.webdriver.common.keys import Keys # Used for controlling script for easier usage
import chromedriver_binary # TODO: Chrome version changes - may require a different version

base_url = config.get('web_scrapping_module', 'base_url')
page_number_str = config.get('web_scrapping_module', 'page')
url_query = '?' + 'q=' + config.get('web_scrapping_module', 'q') + '&' + 'sort=popular'
url = base_url + url_query

# Setup Selenium and Chrome
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')

driver = webdriver.Chrome()
driver.get(url)

page_source = driver.page_source # Obtain dynamically loaded page

soup = BeautifulSoup(page_source, features='lxml') # Indicate HTML parser 

search_results_feed_div = soup.find(id='search-results-feed')
containers = search_results_feed_div.find_all('div', class_= 'feed__container')

recipes_json_list = []

# Create key configuration to grab 100 recipes at a time instead of 20?
for container in containers:
    recipes_list = container.find('ul', class_='feed__items list-unstyled').contents
    for recipe in recipes_list:

        recipe_container = recipe.find('a')

        specific_recipe_url = recipe_container.get('href')
        title = recipe_container.find('div', class_ = 'feed-item__title').text

        new_url = 'https://tasty.co' + specific_recipe_url # TODO: Refactor following code

        # Establish new connection for scraping specific recipe
        driver.get(new_url)
        # Selenium Python script to find button containing nutrition details
        try:
            nutrition_info_button = driver.find_element(by='By.CLASS_NAME', value='nutrition-button') # Click on nutrition info
            if nutrition_info_button.is_displayed():
                driver.execute_script('arguments[0].click();', nutrition_info_button)
                time.sleep(1)
        except Exception:
            pass
            
        page_source = driver.page_source

        soup = BeautifulSoup(page_source, features='html.parser') # Indicate HTML parser

        # Obtain recipe specific image url
        image_url = 'default_image.jpg'
        if soup.find('div', class_='video video--recipe'):
            video_recipe_div_container = soup.find('div', class_='video video--recipe')
            image_full_url = video_recipe_div_container.find('img').get('src')
            image_url = image_full_url.split('?')[0]
        
        # Obtain recipe specific description
        description_str = 'The following recipe has no description.'
        if soup.find('a', class_='link-tasty extra-bold'):
            description_str = soup.find('a', class_='link-tasty extra-bold').text

        # Obtain total cooking time
        total_cooking_time = 0
        if soup.find('p', class_='xs-text-5 extra-bold'):
            total_cooking_time_div = soup.find('p', class_='xs-text-5 extra-bold')
            total_cooking_time_list = total_cooking_time_div.text.split(" ")
            if len(total_cooking_time_list) == 3:
                total_cooking_time_str = total_cooking_time_list[1] + " " + total_cooking_time_list[2]
                total_cooking_time = WebScrapperHelper().convert_timeStr_to_Mins(total_cooking_time_str)
            elif len(total_cooking_time_list) == 2:
                total_cooking_time_str = total_cooking_time_list[0] + " " + total_cooking_time_list[1]
                total_cooking_time = WebScrapperHelper().convert_timeStr_to_Mins(total_cooking_time_str)

        # Obtain list of ingredients
        ingredients_list = []
        if soup.find('div', class_='ingredients__section'):
            ingredients_div = soup.find('div', class_='ingredients__section')
            test = ingredients_div.find('ul', class_='list-unstyled')
            for t in test:
                ingredients_list.append(t.text)

        # Obtain list of preparation steps
        preparation_steps_list = []
        if soup.find('div', class_='preparation'):
            preparation_steps_div = soup.find('div', class_='preparation')
            preparation_steps_ol = soup.find('ol', class_='prep-steps')
            for p in preparation_steps_ol:
                preparation_steps_list.append(p.text)

        # Obtain author for credibility
        author_str = 'Tasty Team'
        if soup.find('div', class_='recipe-attribution'):
            recipe_attribution_div = soup.find('div', class_='recipe-attribution')
            if recipe_attribution_div.find('div', class_='byline extra-bold'):
                author_str = recipe_attribution_div.find('div', class_='byline extra-bold').text

        # Obtain number of servings
        number_of_servings = 0
        if soup.find('p', class_='servings-display'):
            number_of_servings_str = soup.find('p', class_='servings-display').text
            number_of_servings_str_list = number_of_servings_str.split(" ")
            number_of_servings = int(number_of_servings_str_list[1])

        # Obtain recipe dietary requirements
        allowed_dietary_requirements_array = ['vegan', 'vegetarian', 'gluten_free', 'pescatarian'] # To be refactored more to allow more dq options
        dietary_requirements_list = list()

        if soup.find('meta',attrs={'name':'sailthru.tags'}):
            metatags = soup.find('meta',attrs={'name':'sailthru.tags'})
            tags_str = metatags.attrs['content']
            tags_list = tags_str.split(",")
            for tag in tags_list:
                if tag in allowed_dietary_requirements_array:
                    if tag == 'gluten_free':
                        dietary_requirements_list.append('Gluten-Free')
                    else:
                        dietary_requirements_list.append(tag.capitalize())

        # Obtain estimated nutrition per serving
        nutrition_details = {}
        if soup.find('div', class_='nutrition-details'):
            nutrition_details_div = soup.find('div', class_='nutrition-details')
            nutrition_details_soup = nutrition_details_div.find_all('li')
            for nutrition_value in nutrition_details_soup:
                nutrition_text = nutrition_value.text.split(" ")
                key = nutrition_text[0]
                value = nutrition_text[1]
                nutrition_details[key] = value

        # Assume average rating and number of ratings is 0 b/c not found
        # Values can't be None because of recipe sorting algorithm integration..values are required
        average_rating = 0
        number_of_ratings = 0

        # Analyze recipe instructions (Get Ingredient Tag and equipment list)
        steps_str = ''.join(preparation_steps_list)
        ingredients_tag_list, equipment_list = SpoonacularAPI().analyze_recipe_instructions(api_key, steps_str)

        # Classify estimated cuisine
        cuisine_str = SpoonacularAPI().classify_cuisine(api_key, title, ingredients_list)

        # Obtain estimated recipe prices - in forms of USD and GBP
        recipe_price_obj_list = SpoonacularAPI().get_recipe_estimated_price(api_key, ingredients_list, number_of_servings)
        
        # TODO: Append price response
        # Append recipe JSON format
        recipe_json = {
            "title": title,
            "description": description_str,
            "image_url": image_url,
            "total_time": total_cooking_time,
            "author": author_str,
            "default_servings": number_of_servings,
            "dietary_requirements": dietary_requirements_list,
            "nutrition_per_servings": nutrition_details,
            "average_rating": average_rating,
            "number_of_ratings": number_of_ratings,
            "ingredients": ingredients_list,
            "ingredient_tags": ingredients_tag_list,
            "steps": preparation_steps_list,
            "equipment": equipment_list,
            "cuisine": cuisine_str,
            "prices": recipe_price_obj_list,
        }

        recipes_json_list.append(recipe_json)

result = test_recipe_collection.insert_many(recipes_json_list)
