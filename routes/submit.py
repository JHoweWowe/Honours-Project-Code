import mimetypes
import os
from datetime import datetime, timezone

from bson import ObjectId
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from extensions import limiter
from routes.profile import DIETARY_OPTIONS

_ALLOWED_MIME = {'image/jpeg', 'image/png', 'image/webp'}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _resolve_mimetype(file_storage):
    """Return MIME type, falling back to guessing from the filename if the browser sends a generic type."""
    mime = (file_storage.mimetype or '').lower()
    if mime not in _ALLOWED_MIME:
        guessed, _ = mimetypes.guess_type(file_storage.filename or '')
        mime = (guessed or '').lower()
    return mime


def _send_email(to: str, subject: str, html: str) -> None:
    """Fire-and-forget email via Resend. Never raises — email failure must not block submissions."""
    api_key = os.environ.get('RESEND_API_KEY', '')
    if not api_key:
        return
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            'from': 'JustCookIt <noreply@justcookit.app>',
            'to': [to],
            'subject': subject,
            'html': html,
        })
    except Exception:
        pass


def _upload_image(file_storage):
    """Upload a werkzeug FileStorage to Cloudinary. Returns secure_url or None on failure."""
    if not file_storage or not file_storage.filename:
        return None
    mime = _resolve_mimetype(file_storage)
    if mime not in _ALLOWED_MIME:
        current_app.logger.warning('Image upload rejected: unrecognised MIME type %r for file %r', mime, file_storage.filename)
        return None
    data = file_storage.read()
    if len(data) > _MAX_IMAGE_BYTES:
        current_app.logger.warning('Image upload rejected: file size %d bytes exceeds 5 MB limit', len(data))
        return None
    try:
        import cloudinary
        import cloudinary.uploader
        if not cloudinary.config().cloud_name:
            cloudinary_url = os.environ.get('CLOUDINARY_URL', '')
            if cloudinary_url:
                cloudinary.config(cloudinary_url=cloudinary_url)
            else:
                current_app.logger.error('Image upload failed: CLOUDINARY_URL env var is not set')
                return None
        result = cloudinary.uploader.upload(
            data,
            folder='justcookit/user_recipes',
            resource_type='image',
        )
        return result.get('secure_url')
    except Exception:
        current_app.logger.exception('Cloudinary upload failed')
        return None

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
@limiter.limit('3 per day', key_func=lambda: str(current_user.id))
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

    image_file = request.files.get('image')
    image_url = _upload_image(image_file)
    if image_file and image_file.filename and image_url is None:
        flash('Image could not be uploaded — recipe saved without a photo.', 'warning')

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
        admin_email = current_app.config.get('ADMIN_EMAILS', ['howejust@gmail.com'])[0]
        _send_email(
            to=admin_email,
            subject=f'[JustCookIt] New recipe pending review: {title}',
            html=(
                f'<p><b>{current_user.email}</b> submitted a new recipe: <b>{title}</b>.</p>'
                f'<p><a href="https://justcookit.herokuapp.com/admin/recipes">Review on admin page</a></p>'
            ),
        )
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
    mongo = current_app.mongo
    doc = mongo.db.user_recipes.find_one({'_id': oid}, {'submitted_by': 1, 'title': 1})
    mongo.db.user_recipes.update_one(
        {'_id': oid},
        {'$set': {'status': 'approved', 'moderation_note': None}},
    )
    if doc and doc.get('submitted_by'):
        user = mongo.db.users.find_one({'_id': doc['submitted_by']}, {'email': 1})
        if user and user.get('email'):
            _send_email(
                to=user['email'],
                subject='[JustCookIt] Your recipe has been approved!',
                html=(
                    f'<p>Great news! Your recipe <b>{doc.get("title", "")}</b> has been approved '
                    f'and is now live on JustCookIt.</p>'
                    f'<p><a href="https://justcookit.herokuapp.com/my-submissions">View your submissions</a></p>'
                ),
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
    mongo = current_app.mongo
    doc = mongo.db.user_recipes.find_one({'_id': oid}, {'submitted_by': 1, 'title': 1})
    mongo.db.user_recipes.update_one(
        {'_id': oid},
        {'$set': {'status': 'rejected', 'moderation_note': note}},
    )
    if doc and doc.get('submitted_by'):
        user = mongo.db.users.find_one({'_id': doc['submitted_by']}, {'email': 1})
        if user and user.get('email'):
            note_html = f'<p>Reason: {note}</p>' if note else ''
            _send_email(
                to=user['email'],
                subject='[JustCookIt] Update on your recipe submission',
                html=(
                    f'<p>Your recipe <b>{doc.get("title", "")}</b> was not approved at this time.</p>'
                    f'{note_html}'
                    f'<p><a href="https://justcookit.herokuapp.com/my-submissions">View your submissions</a></p>'
                ),
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
