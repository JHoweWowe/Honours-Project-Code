from bson import json_util, ObjectId
import json

from flask import Flask, render_template
from flask_pymongo import PyMongo

app = Flask(__name__)
mongo = PyMongo(app, uri="mongodb://localhost:27017/honours-proj-website-recipes")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def meow():
    test = mongo.db.bbcgoodfood.find({"title": "Halloumi flatbreads"})
    first = list(test)[0]
    page_sanitized = json.loads(json_util.dumps(first))
    return page_sanitized