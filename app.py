from flask import Flask, render_template, Response, request
from flask_pymongo import PyMongo, pymongo
from pymongo import TEXT
from bson.objectid import ObjectId

import configparser, json

app = Flask(__name__)
#mongo = PyMongo(app, uri="mongodb://localhost:27017/honours-proj-website-recipes")

config = configparser.ConfigParser()
config.read('settings.ini')

base_uri = 'mongodb+srv://'
username = config.get('food_recipe_database', 'username')
password = config.get('food_recipe_database', 'password')
uri = base_uri + username + ':' + password + '@honours-project.x6odc.mongodb.net/db?retryWrites=true&w=majority'

mongo = pymongo.MongoClient(uri)

# THIS IS DEFINITELY NOT GOOD PRACTICE - POSSIBLY BASED ON HIGHEST RANKING AND DIETARY REQUIREMENTS???
featured_recipes_data = list(mongo.db.bbcgoodfood.find({'average_rating': { '$gt': 4.4, '$lt': 5}}).sort('number_of_ratings', -1).limit(3))

mongo.db.bbcgoodfood.create_index([('title',TEXT), ('description', TEXT)],default_language ="english") # Enable text search

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', featured_recipes_data = featured_recipes_data)

@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        collection = []
        sample_dict_size = dict()
        sample_dict_size["$sample"] = {"size" : 6} # RANDOM SAMPLE SIZE - can easily be customizable
        
        match_requirements = dict()
        match_inner_requirements = dict()

        if request.args.get('cooking-time-range') != '0':
            time = int(request.args.get('cooking-time-range'))
            match_inner_requirements['total_time'] = { "$lte": time }

        if request.args.get('dietary-requirements-dropdown') != None:
            match_inner_requirements['dietary_requirements'] = request.args.get('dietary-requirements-dropdown')

        if request.args.get('include-ingredients') != '':
            included_ingredients_list = request.args.get('include-ingredients').split(",") # Tokenization...
            match_inner_requirements['ingredient_tags'] = { "$in": included_ingredients_list }
        
        if request.args.get('exclude-ingredients') != '':
            excluded_ingredients_list = request.args.get('exclude-ingredients').split(",")
            if match_inner_requirements.get('ingredient_tags') != None:
                match_inner_requirements['ingredient_tags']["$nin"] = excluded_ingredients_list
            else:
                match_inner_requirements['ingredient_tags'] = {"$nin": excluded_ingredients_list }

        search_query = request.args.get('q', None)
        if search_query:
            print(search_query)
            search_query_str = '\"' + str(search_query) + '\"'
            match_inner_requirements['$text'] = { "$search": search_query_str }


        if len(match_inner_requirements) > 0:
            match_requirements["$match"] = match_inner_requirements
            collection.append(match_requirements)

        collection.append(sample_dict_size)
        
        data = list(mongo.db.bbcgoodfood.aggregate(collection))

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