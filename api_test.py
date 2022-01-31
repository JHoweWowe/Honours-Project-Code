# Temporary file to test API endpoints connecting to server and good coding safety practice
import requests, configparser, os

config = configparser.ConfigParser()

def write_file():
    config.write(open('settings.ini', 'w'))

if not os.path.exists('settings.ini'):
    config['api_keys'] = {'spoonacular_api_key': 'write_your_api_key_here'}
    write_file()

else:
    config.read('settings.ini')

    print(config.get('api_keys', 'spoonacular_api_key'))


def analyzeRecipeInstructions(instructions):

    api_key = config.get('api_keys', 'spoonacular_api_key')
    base_url = 'https://api.spoonacular.com/recipes/analyzeInstructions'

    params = {
        'apiKey': api_key,
        'instructions': instructions
    }
    # TODO: Check if above keys exist...

    url = base_url + '?' + 'apiKey=' + params['apiKey'] + '&' + 'instructions=' + params['instructions']

    r = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"})
    results = r.json() # Only show if response code is 200, otherwise return None available
    ingredients_list = results['ingredients']
    equipment_list = results['equipment']
    for ingredient in ingredients_list:
        print(ingredient['name'])
    print('YEET')
    for equipment in equipment_list:
        print(equipment['name'])

# Basic code execution
test_instructions = 'Heat 2 tbsp of the oil in a saucepan over a medium heat. Fry the onion with a pinch of salt for 7 mins. Add the garlic, chilli and rosemary, and cook for 1 min more. Tip in the tomatoes and sugar, and simmer for 20 mins. Heat the remaining oil in a medium frying pan over a medium heat. Squeeze the sausagemeat from the skins and fry, breaking it up with a wooden spoon, for 5-7 mins until golden. Add to the sauce with the milk and lemon zest, then simmer for a further 5 mins. To freeze, leave to cool completely and transfer to large freezerproof bags. Cook the pasta following pack instructions. Drain and toss with the sauce. Scatter over the parmesan and parsley leaves to serve.'
analyzeRecipeInstructions(test_instructions)