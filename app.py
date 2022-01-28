from flask import Flask, render_template, Response, request, redirect
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

import json

app = Flask(__name__)
mongo = PyMongo(app, uri="mongodb://localhost:27017/honours-proj-website-recipes")

# THIS IS DEFINITELY NOT GOOD PRACTICE - POSSIBLY BASED ON HIGHEST RANKING AND DIETARY REQUIREMENTS???
featured_recipes_data = list(mongo.db.bbcgoodfood.find({'average_rating': { '$gt': 4.4, '$lt': 5}}).sort('number_of_ratings', -1).limit(3))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', featured_recipes_data = featured_recipes_data)

# Refactor - filters as arguments
@app.route('/', methods=['POST'])
def search_recipes():
    requirements = dict()
    filters = dict()

    time_str = request.form.get('total-cooking-time', default='')
    dietary_requirements_str = request.form.get('dietary-requirements-dropdown', default='')

    if time_str != '':
        requirements['total_time'] = int(time_str)
    if dietary_requirements_str != '':
        requirements['dietary_requirements'] = dietary_requirements_str
    
    print('Dietary Requirements: ' + str(requirements))

    return test_get_recipe_data(requirements)

def quick_search_recipes():
    # TODO: Create quick search functionality
    pass

@app.route('/test-route-recipes', methods=['GET'])
def test_get_recipe_data(requirements):
    try:
        #data = list(mongo.db.bbcgoodfood.find({"time": time})) # Takes recipes with 50 mins

        data = list(mongo.db.bbcgoodfood.aggregate([
            {"$match": requirements},
            {"$sample": {"size": 3}}, # Just a test
        ]))

        for recipe in data:
            recipe["_id"] = str(recipe["_id"])
        return render_template('recipes.html', data=data, featured_recipes_data = featured_recipes_data)

    except Exception as ex:
        print(ex)
        return Response(response= json.dumps({"message": "cannot read recipes"}), status=500, mimetype="application/json")

# Routing for a specific recipe - perhaps add it as URL, pass recipe as parameter
@app.route('/recipe/<id>', methods=['GET'])
def view_recipe(id):
    recipe_data = mongo.db.bbcgoodfood.find_one({"_id": ObjectId(id)})
    return render_template('recipe.html', id=id, recipe_data = recipe_data) # Data passed redudantly