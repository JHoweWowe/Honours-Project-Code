from datetime import datetime, timezone

from bson import ObjectId
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from routes.profile import DIETARY_OPTIONS

bp = Blueprint('submit', __name__)


def _build_cuisines(mongo):
    raw = mongo.db.bbcgoodfood.distinct('cuisine') + mongo.db.tasty.distinct('cuisine')
    return sorted({c for c in raw if c and c.strip()})


def _require_admin():
    if not current_user.is_authenticated or current_user.email not in current_app.config['ADMIN_EMAILS']:
        abort(403)


@bp.route('/submit-recipe', methods=['GET'])
@login_required
def submit_form():
    mongo = current_app.mongo
    return render_template(
        'submit_recipe.html',
        cuisines=_build_cuisines(mongo),
        dietary_options=DIETARY_OPTIONS,
    )


@bp.route('/submit-recipe', methods=['POST'])
@login_required
def submit_recipe():
    mongo = current_app.mongo
    errors = []

    title = request.form.get('title', '').strip()
    if not title:
        errors.append('Recipe title is required.')
    elif len(title) > 100:
        errors.append('Title must be 100 characters or fewer.')

    raw_ingredients = request.form.get('ingredients', '').strip()
    if not raw_ingredients:
        errors.append('Ingredients are required.')

    raw_steps = request.form.get('steps', '').strip()
    if not raw_steps:
        errors.append('Method / steps are required.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('submit.submit_form'))

    ingredients = [line.strip() for line in raw_ingredients.splitlines() if line.strip()]
    steps = [line.strip() for line in raw_steps.splitlines() if line.strip()]

    cuisine = request.form.get('cuisine', '').strip() or None

    total_time = None
    raw_time = request.form.get('total_time', '').strip()
    if raw_time:
        try:
            total_time = int(raw_time)
        except ValueError:
            pass

    servings = 2
    raw_servings = request.form.get('servings', '').strip()
    if raw_servings:
        try:
            servings = max(1, int(raw_servings))
        except ValueError:
            pass

    dietary_tags = [d for d in request.form.getlist('dietary_tags') if d in DIETARY_OPTIONS]

    image_url = request.form.get('image_url', '').strip() or None

    is_admin = current_user.email in current_app.config.get('ADMIN_EMAILS', [])
    status = 'approved' if is_admin else 'pending'

    mongo.db.user_recipes.insert_one({
        'title': title,
        'ingredients': ingredients,
        'steps': steps,
        'cuisine': cuisine,
        'dietary_requirements': dietary_tags,
        'total_time': total_time,
        'image_url': image_url,
        'servings': servings,
        'submitted_by': ObjectId(current_user.id),
        'submitted_at': datetime.now(timezone.utc),
        'status': status,
        'moderation_note': None,
        'source': 'user',
    })

    if is_admin:
        flash('Recipe submitted and published immediately.', 'success')
    else:
        flash('Recipe submitted! It will appear in search results after review.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/admin/recipes', methods=['GET'])
@login_required
def admin_recipes():
    _require_admin()
    mongo = current_app.mongo
    pending = list(
        mongo.db.user_recipes.find({'status': 'pending'}).sort('submitted_at', -1)
    )
    user_ids = [doc['submitted_by'] for doc in pending if doc.get('submitted_by')]
    users = {
        doc['_id']: doc.get('display_name', 'Unknown')
        for doc in mongo.db.users.find({'_id': {'$in': user_ids}})
    }
    for doc in pending:
        doc['submitter_name'] = users.get(doc.get('submitted_by'), 'Unknown')
    return render_template('admin_recipes.html', recipes=pending)


@bp.route('/admin/recipes/<recipe_id>/approve', methods=['POST'])
@login_required
def approve_recipe(recipe_id):
    _require_admin()
    try:
        oid = ObjectId(recipe_id)
    except Exception:
        abort(400)
    current_app.mongo.db.user_recipes.update_one(
        {'_id': oid},
        {'$set': {'status': 'approved', 'moderation_note': None}},
    )
    flash('Recipe approved.', 'success')
    return redirect(request.referrer or url_for('submit.admin_recipes'))


@bp.route('/admin/recipes/<recipe_id>/reject', methods=['POST'])
@login_required
def reject_recipe(recipe_id):
    _require_admin()
    try:
        oid = ObjectId(recipe_id)
    except Exception:
        abort(400)
    note = request.form.get('moderation_note', '').strip() or None
    current_app.mongo.db.user_recipes.update_one(
        {'_id': oid},
        {'$set': {'status': 'rejected', 'moderation_note': note}},
    )
    flash('Recipe rejected.', 'warning')
    return redirect(request.referrer or url_for('submit.admin_recipes'))


@bp.route('/my-submissions', methods=['GET'])
@login_required
def my_submissions():
    mongo = current_app.mongo
    submissions = list(
        mongo.db.user_recipes
        .find({'submitted_by': ObjectId(current_user.id)})
        .sort('submitted_at', -1)
    )
    return render_template('my_submissions.html', submissions=submissions)
