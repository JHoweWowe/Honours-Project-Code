# TODO: Categorize under API folder if other additional APIs are needed
# Following class sets up Spoonacular API and handles calls

from bs4 import BeautifulSoup # Required for parsing HTML text for recipe estimated price
import re, requests, unidecode # unidecode used to decode unexpected text

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

    # NOTE: HTML response returning visualization within CanvasJS doesn't work and is ugly
    # Endpoint call to return HTML response for estimated recipe price
    def get_recipe_estimated_price(self, api_key, ingredients_list, servings):
        
        base_url = 'https://api.spoonacular.com/recipes/visualizePriceEstimator'

        ingredients_list_str = ''.join([ingredient + '\n' for ingredient in ingredients_list])

        # TODO: Reconfigure params - showBacklink, defaultCss
        params = {
            'apiKey': api_key,
            'ingredientList': ingredients_list_str,
            'servings': servings,
            'defaultCss': False,
            'showBacklink': True,
            'language': 'en'
        }

        r = requests.post(url=base_url, params=params, headers={
            'Accept': 'text/html',
            "Content-Type": "application/x-www-form-urlencoded"
        })

        # Check response status code validity
        if r.status_code == 200:
            html_text = r.text
            soup = BeautifulSoup(html_text, features='html.parser') # Indicate HTML parser

            recipe_price_obj_list = list()

            # Tricky because divs are not labelled properly
            if soup.find('div', id='spoonacularPriceBreakdownTable'):
                spoonacular_price_breakdown_table_div = soup.find('div', id='spoonacularPriceBreakdownTable')
                    
                # Obtain overall USD price
                price_str = spoonacular_price_breakdown_table_div.contents[0].text
                test = '\$([0-9,]*\.[0-9]*)'

                match = re.search(test, price_str)

                price_float = float(match.group(1))

                price_usd_obj = {}
                price_usd_obj['currency'] = 'USD'
                price_usd_obj['overall_cost_per_serving'] = price_float
                
                price_usd_obj_ingredients = dict()
                price_gbp_obj_ingredients = dict()

                price_gbp_obj = {}
                price_gbp_obj['currency'] = 'GBP'
                # Conversion from USD to GBP
                price_gbp_obj['overall_cost_per_serving'] = round(price_float * 0.77, 2)

                # Obtain ingredients and cost of each ingredient respectively
                ingredient_name_div = spoonacular_price_breakdown_table_div.contents[2]
                ingredient_cost_div = spoonacular_price_breakdown_table_div.contents[3]
                ingredient_name_cost_list = list(zip(ingredient_name_div, ingredient_cost_div))

                # Check if recipe USD cost exists
                for name, cost in ingredient_name_cost_list:

                    # Remove any Latin-1 Supplement characters except for fractions
                    name_str = re.sub('[\xA0-\xBB\xC0-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]', '', name.text)

                    cost_str = cost.text
                    if cost_str.startswith('$'):
                        cost_str_usd_value = cost_str[1:]
                        cost_usd_value = float(cost_str_usd_value)
                        price_usd_obj_ingredients[name_str] = cost_usd_value

                        cost_gbp_value = round(cost_usd_value * 0.77, 2)
                        price_gbp_obj_ingredients[name_str] = cost_gbp_value

                overall_usd_cost = round(sum(price_usd_obj_ingredients.values()), 2)
                overall_gbp_cost = round(sum(price_gbp_obj_ingredients.values()), 2)

                price_usd_obj['overall_cost'] = overall_usd_cost
                price_gbp_obj['overall_cost'] = overall_gbp_cost

                price_usd_obj['ingredients_name_cost_list'] = price_usd_obj_ingredients
                price_gbp_obj['ingredients_name_cost_list'] = price_gbp_obj_ingredients

                recipe_price_obj_list.append(price_usd_obj)
                recipe_price_obj_list.append(price_gbp_obj)

                return recipe_price_obj_list

        else:
            return list()
 