import re
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

bp = Blueprint('profile', __name__, url_prefix='/profile')

DIETARY_OPTIONS = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Pescatarian', 'Dairy-Free', 'Nut-Free', 'Halal']
SKILL_LEVELS = ['beginner', 'intermediate', 'advanced']
COOK_FREQS = ['rarely', 'sometimes', 'somewhat often', 'often', 'daily']


def _build_cuisines(mongo):
    raw = mongo.db.bbcgoodfood.distinct('cuisine') + mongo.db.tasty.distinct('cuisine')
    return sorted({c for c in raw if c and c.strip()})


@bp.route('/', methods=['GET'])
@login_required
def view():
    mongo = current_app.mongo
    user_doc = mongo.db.users.find_one({'_id': ObjectId(current_user.id)}) or {}

    dob_str = ''
    if user_doc.get('dob'):
        dob_str = user_doc['dob'].strftime('%Y-%m-%d')

    return render_template(
        'profile.html',
        user_doc=user_doc,
        dob_str=dob_str,
        cuisines=_build_cuisines(mongo),
        dietary_options=DIETARY_OPTIONS,
        skill_levels=SKILL_LEVELS,
        cook_freqs=COOK_FREQS,
    )


@bp.route('/', methods=['POST'])
@login_required
def update():
    mongo = current_app.mongo
    errors = []

    first_name = request.form.get('first_name', '').strip()
    if not first_name:
        errors.append('First name is required.')

    dob = None
    raw_dob = request.form.get('dob', '').strip()
    if raw_dob:
        try:
            dob = datetime.strptime(raw_dob, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            errors.append('Date of birth must be a valid date.')

    max_budget = None
    raw_budget = request.form.get('max_budget_gbp', '').strip()
    if raw_budget:
        try:
            max_budget = float(raw_budget)
            if max_budget <= 0:
                errors.append('Max budget must be greater than 0.')
        except ValueError:
            errors.append('Max budget must be a number.')

    household_size = None
    raw_hs = request.form.get('household_size', '').strip()
    if raw_hs:
        try:
            household_size = int(raw_hs)
            if not (1 <= household_size <= 20):
                errors.append('Household size must be between 1 and 20.')
        except ValueError:
            errors.append('Household size must be a whole number.')

    dietary_prefs = [d for d in request.form.getlist('dietary_prefs') if d in DIETARY_OPTIONS]
    preferred_cuisines = request.form.getlist('preferred_cuisines')

    skill_level = request.form.get('skill_level', '').strip()
    if skill_level not in SKILL_LEVELS:
        skill_level = ''

    cooking_frequency = request.form.get('cooking_frequency', '').strip()
    if cooking_frequency not in COOK_FREQS:
        cooking_frequency = ''

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('profile.view'))

    location = request.form.get('location', '').strip()

    postcode = request.form.get('postcode', '').strip().upper()
    if postcode and not re.match(r'^[A-Z0-9 ]{3,10}$', postcode):
        errors.append('Invalid postcode format.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('profile.view'))

    payload = {
        'first_name': first_name,
        'display_name': first_name,
        'dietary_prefs': dietary_prefs,
        'preferred_cuisines': preferred_cuisines,
        'location': location,
        'postcode': postcode,
        'profile_updated_at': datetime.now(timezone.utc),
    }
    if dob is not None:
        payload['dob'] = dob
    if max_budget is not None:
        payload['max_budget_gbp'] = max_budget
    if household_size is not None:
        payload['household_size'] = household_size
    if skill_level:
        payload['skill_level'] = skill_level
    if cooking_frequency:
        payload['cooking_frequency'] = cooking_frequency

    mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': payload})

    flash('Profile saved!', 'success')
    return redirect(url_for('profile.view'))
