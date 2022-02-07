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

    # TODO: Complete function acting as an endpoint call
    def another_function():
        pass
