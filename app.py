from flask import Flask, render_template, Response, request, redirect, url_for
from flask_pymongo import PyMongo, pymongo
from pymongo import TEXT
from bson.objectid import ObjectId

import json

app = Flask(__name__)
mongo = PyMongo(app, uri="mongodb://localhost:27017/honours-proj-website-recipes")

# THIS IS DEFINITELY NOT GOOD PRACTICE - POSSIBLY BASED ON HIGHEST RANKING AND DIETARY REQUIREMENTS???
featured_recipes_data = list(mongo.db.bbcgoodfood.find({'average_rating': { '$gt': 4.4, '$lt': 5}}).sort('number_of_ratings', -1).limit(3))

mongo.db.bbcgoodfood.create_index([('title',TEXT), ('description', TEXT)],default_language ="english") # Enable text search

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', featured_recipes_data = featured_recipes_data)

@app.route('/search', methods=['GET'])
def search():

    try:
        requirements = dict()
        time_str = request.args.get('total-cooking-time')
        dietary_requirements_str = request.args.get('dietary-requirements-dropdown')

        if time_str != '':
            requirements['total_time'] = int(time_str)

        if dietary_requirements_str != None:
            requirements['dietary_requirements'] = dietary_requirements_str

        data = list(mongo.db.bbcgoodfood.aggregate(
            [
                {"$match": requirements},
                {"$sample": {"size": 3}} # Max size is 3...just a test
            ]
        ))

        if request.args.get('q') != '':

            search_query_str = '\"' + str(request.args.get('q')) + '\"'
            data = list(mongo.db.bbcgoodfood.aggregate(
                [
                    {"$match": {"$text": { "$search": search_query_str}}},
                    {"$match": requirements},
                    {"$sample": {"size": 3}} # Max size is 3...just a test
                ]
            ))

        return render_template('recipes.html', data=data, featured_recipes_data = featured_recipes_data)

    except Exception as ex:
        print(ex)
        return Response(response= json.dumps({"message": "cannot read recipes"}), status=500, mimetype="application/json")

# TODO: Complete show filter by...
def show_by_filters():
    pass

# Routing for a specific recipe - perhaps add it as URL, pass recipe as parameter
@app.route('/recipe/<id>', methods=['GET'])
def view_recipe(id):
    recipe_data = mongo.db.bbcgoodfood.find_one({"_id": ObjectId(id)})
    return render_template('recipe.html', id=id, recipe_data = recipe_data) # Data passed redudantly