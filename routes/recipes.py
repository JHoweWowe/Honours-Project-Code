from flask import Blueprint, render_template, current_app
from bson.objectid import ObjectId

from routes.stores import COUNTRIES

bp = Blueprint('recipes', __name__)


@bp.route('/recipe/<id>', methods=['GET'])
def view_recipe(id):
    mongo = current_app.mongo
    oid = ObjectId(id)

    recipe_data = mongo.db.bbcgoodfood.find_one({'_id': oid})
    if recipe_data is None:
        recipe_data = mongo.db.tasty.find_one({'_id': oid})
    if recipe_data is None:
        recipe_data = mongo.db.user_recipes.find_one({'_id': oid, 'status': 'approved'})
        if recipe_data and recipe_data.get('submitted_by'):
            user = mongo.db.users.find_one({'_id': recipe_data['submitted_by']}, {'display_name': 1})
            recipe_data['submitter_name'] = user.get('display_name', 'Community Member') if user else 'Community Member'

    related = []
    if recipe_data and recipe_data.get('cuisine'):
        cuisine = recipe_data['cuisine']
        related = list(
            mongo.db.bbcgoodfood.find({'cuisine': cuisine, '_id': {'$ne': oid}}).limit(3)
        )
        if len(related) < 3:
            related += list(
                mongo.db.tasty.find(
                    {'cuisine': cuisine, '_id': {'$ne': oid}}
                ).limit(3 - len(related))
            )

    return render_template('recipe.html', id=id, recipe_data=recipe_data or {}, related=related, countries=COUNTRIES)
