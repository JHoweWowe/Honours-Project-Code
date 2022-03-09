# TODO: Categorize under API folder if other additional APIs are needed
# Following class sets up Spoonacular API and handles calls 
import requests

class SpoonacularAPI():

    # Endpoint call for analyzing recipe instructions (or obtain equipment)
    def analyze_recipe_instructions(self, api_key, instructions):

        base_url = 'https://api.spoonacular.com/recipes/analyzeInstructions'

        params = {
            'apiKey': api_key,
            'instructions': instructions
        }
        # TODO: Check if above keys exist...

        url = base_url + '?' + 'apiKey=' + params['apiKey'] + '&' + 'instructions=' + params['instructions']

        r = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"})

        # Check response status code validity
        if r.status_code == 200:
            results = r.json()
            ingredients_list_dict = results['ingredients']
            ingredients_tag_list = []

            equipment_list_dict = results['equipment']
            equipment_list = []

            for ingredients_dict in ingredients_list_dict:
                ingredients_tag_list.append(ingredients_dict['name'])

            for equipment_dict in equipment_list_dict:
                equipment_list.append(equipment_dict['name'])

            return ingredients_tag_list, equipment_list
        else:
            return tuple([], [])

    # Endpoint call to classify recipe's cuisine
    def classify_cuisine(self, api_key, recipe_title, ingredients_list):

        base_url = 'https://api.spoonacular.com/recipes/cuisine'

        ingredients_list_str = ''.join([ingredient + '\n' for ingredient in ingredients_list])

        params = {
            'apiKey': api_key,
            'title': recipe_title,
            'ingredientList': ingredients_list_str,
            'language': 'en'
        }

        url = base_url + '?' + 'apiKey=' + params['apiKey'] + '&' + 'title=' + params['title'] + '&' + 'ingredientList=' + params['ingredientList'] + '&' + 'language=' + params['language']

        r = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"})

        # Check response status code validity
        if r.status_code == 200:
            results = r.json()
            main_cuisine = results['cuisine']
            secondary_cuisines = results['cuisines']
            confidence = results['confidence']
            
            return main_cuisine
        else:
            return None

    # Endpoint call to show estimated price
    def get_recipe_estimated_price(self, api_key, ingredient_list, servings):
        # Set mode, defaultCss, showBacklink, language accordingly
        pass