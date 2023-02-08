from flask import Flask, render_template, Response, request
from flask_pymongo import pymongo
from pymongo import TEXT
from bson.objectid import ObjectId

import configparser, json

app = Flask(__name__, static_url_path="", static_folder="static")

config = configparser.ConfigParser()
config.read('settings.ini')

base_uri = 'mongodb+srv://'
username = config.get('food_recipe_database', 'username')
password = config.get('food_recipe_database', 'password')
hostname = config.get('food_recipe_database', 'hostname')
uri = base_uri + username + ':' + password + '@' + hostname + '/db?retryWrites=true&w=majority'
#uri = 'mongodb://localhost:27017/?readPreference=primary&directConnection=true&ssl=false'

mongo = pymongo.MongoClient(uri)

# TODO: Refactor this in search function instead?
mongo.db.bbcgoodfood.create_index([('title',TEXT), ('description', TEXT)],default_language ="english") # Enable text search
mongo.db.tasty.create_index([('title',TEXT), ('description', TEXT)],default_language ="english") # Enable text search

@app.route('/', methods=['GET', 'POST'])
def index():
    # ASSUME FEATURED RECIPES HAVE AVG RATING BETWEEN 4.4 AND 4.9 AND SORTED BY NUMBER OF RATINGS DESCENDING
    featured_recipes_data = list(mongo.db.bbcgoodfood.find({'average_rating': { '$gt': 4.4, '$lt': 5}}).sort('number_of_ratings', -1).limit(3))
    return render_template('index.html', featured_recipes_data = featured_recipes_data)

# Order - $match, $sort, $group
@app.route('/search', methods=['GET', 'POST'])
def search():
    collection = []
    sample_dict_size = dict()
    sample_dict_size["$sample"] = {"size" : 6} # RANDOM SAMPLE SIZE - can easily be customizable
    
    match_requirements = dict()
    match_inner_requirements = dict()

    # Initalize default params
    time = 0
    dietary_requirements_list = list() 
    include = ''
    exclude = ''
    sort = 'relevance' # By default

    if request.args.get('time') != '0':
        time = int(request.args.get('time'))
        match_inner_requirements['total_time'] = { "$lte": time }
    
    # Check which dietary requirements are requested - TODO: Refactor this as a function
    if request.args.get('dq'):
        dietary_requirements_list.append(request.args.get('dq'))
    if len(dietary_requirements_list) > 0:
        match_inner_requirements['dietary_requirements'] = { "$in": dietary_requirements_list }

    if request.args.get('include'):
        include = request.args.get('include')
        ingredients_list = include.split(',')

        match_inner_requirements['ingredient_tags'] = { "$in": ingredients_list }
    
    if request.args.get('exclude'):
        exclude = request.args.get('exclude')
        excluded_ingredients_list = exclude.split(',')
        if match_inner_requirements.get('ingredient_tags') != None:
            match_inner_requirements['ingredient_tags']["$nin"] = excluded_ingredients_list
        else:
            match_inner_requirements['ingredient_tags'] = {"$nin": excluded_ingredients_list }

    query_str = ''
    if request.args.get('q'):
        query_str = request.args.get('q')
        search_query_str = '\"' + str(query_str) + '\"'
        match_inner_requirements['$text'] = { "$search": search_query_str }

    if len(match_inner_requirements) > 0:
        match_requirements["$match"] = match_inner_requirements
        collection.append(match_requirements)
        
    collection.append(sample_dict_size)

    # Optional sort aggregate function for recipes
    sort_requirements = dict()
    if request.args.get('sort'):
        if request.args.get('sort') == 'rating':
            sort_requirements['$sort'] = { 'average_rating': -1 }
            collection.append(sort_requirements)
        elif request.args.get('sort') == 'popularity':
            sort_requirements['$sort'] = { 'number_of_ratings': -1 }
            collection.append(sort_requirements)
        elif request.args.get('sort') == 'time':
            sort_requirements['$sort'] = { 'total_time': 1 }
            collection.append(sort_requirements)

    # Obtain recipes from each food recipe collection
    bbc_good_food_data = list(mongo.db.bbcgoodfood.aggregate(collection))
    tasty_recipes_data = list(mongo.db.tasty.aggregate(collection)) # Obtain two lists

    data = bbc_good_food_data + tasty_recipes_data # TODO: Could shuffle following data

    return render_template(
        'recipes.html',
        data=data,
        query=query_str,
        time=time,
        dq=dietary_requirements_list,
        include=include,
        exclude=exclude,
        sort=sort
    )


# Routing for a specific recipe - perhaps add it as URL, pass recipe as parameter
@app.route('/recipe/<id>', methods=['GET'])
def view_recipe(id):
    # Determine which collection to use
    if mongo.db.bbcgoodfood.find_one({"_id": ObjectId(id)}) is not None:
        recipe_data = mongo.db.bbcgoodfood.find_one({"_id": ObjectId(id)})
    elif mongo.db.tasty.find_one({"_id": ObjectId(id)}) is not None:
        recipe_data = mongo.db.tasty.find_one({"_id": ObjectId(id)})
    else:
        recipe_data = mongo.db.bbcgoodfood.find_one({"_id": ObjectId(id)})

    return render_template('recipe.html', id=id, recipe_data = recipe_data) # Data passed redudantly

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000) # Change port number for future purposes
