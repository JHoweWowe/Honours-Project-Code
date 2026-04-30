from flask import Flask, render_template, Response, request, redirect
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

import json

app = Flask(__name__)
mongo = PyMongo(app, uri="mongodb://localhost:27017/honours-proj-website-recipes")

@app.route('/')
def index():
    return render_template('index.html')

# Test with filters as arguments
@app.route('/', methods=['POST'])
def search_recipes():
    filters = []
    time = request.form['cooking-time']
    print(time)
    #return get_recipe_data(time)
    return test_get_recipe_data(time)

@app.route('/test-route-recipes', methods=['GET'])
def test_get_recipe_data(time):
    #return render_template('comments.html', comments=test_comments)
    try:
        data = list(mongo.db.bbcgoodfood.find({"time": time})) # Takes recipes with 50 mins
        for recipe in data:
            recipe["_id"] = str(recipe["_id"])
        return render_template('recipes.html', data=data)

    except Exception as ex:
        print(ex)
        return Response(response= json.dumps({"message": "cannot read recipes"}), status=500, mimetype="application/json")

# Routing for a specific recipe - perhaps add it as URL, pass recipe as parameter
@app.route('/recipe/<id>', methods=['GET'])
def view_recipe(id):
    recipe_data = mongo.db.bbcgoodfood.find_one({"_id": ObjectId(id)})
    return render_template('recipe.html', id=id, recipe_data = recipe_data) # Data passed redudantly