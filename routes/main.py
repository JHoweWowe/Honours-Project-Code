import math

from flask import Blueprint, render_template, request, current_app
from flask_login import current_user
from extensions import cache

bp = Blueprint('main', __name__)

PER_PAGE = 6

# Fields needed for recipe cards — keeps documents small across all queries
_CARD_PROJECT = {
    '_id': 1, 'title': 1, 'image_url': 1, 'cuisine': 1,
    'prices': 1, 'total_time': 1, 'average_rating': 1,
    'number_of_ratings': 1, 'dietary_requirements': 1, 'description': 1,
}


def _get_top_cuisines(mongo, n=5):
    pipeline = [
        {'$match': {'cuisine': {'$nin': [None, '']}}},
        {'$group': {'_id': '$cuisine', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': n},
    ]
    counts = {}
    for doc in list(mongo.db.bbcgoodfood.aggregate(pipeline)) + list(mongo.db.tasty.aggregate(pipeline)):
        counts[doc['_id']] = counts.get(doc['_id'], 0) + doc['count']
    return [c for c, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]]


def _get_cached_cuisines(mongo):
    cuisines = cache.get('all_cuisines')
    if cuisines is None:
        raw = (
            mongo.db.bbcgoodfood.distinct('cuisine') +
            mongo.db.tasty.distinct('cuisine') +
            mongo.db.user_recipes.distinct('cuisine', {'status': 'approved'})
        )
        cuisines = sorted({c for c in raw if c and c.strip()})
        cache.set('all_cuisines', cuisines, timeout=1800)
    return cuisines


def _get_cached_top_cuisines(mongo, n=5):
    top = cache.get('top_cuisines')
    if top is None:
        top = _get_top_cuisines(mongo, n)
        cache.set('top_cuisines', top, timeout=1800)
    return top


@bp.route('/', methods=['GET'])
@cache.cached(timeout=1800, key_prefix='index', unless=lambda: current_user.is_authenticated)
def index():
    mongo = current_app.mongo
    featured = list(
        mongo.db.bbcgoodfood
        .find({'average_rating': {'$gt': 4.4, '$lt': 5}}, _CARD_PROJECT)
        .sort('number_of_ratings', -1)
        .limit(3)
    )
    cuisines = _get_cached_cuisines(mongo)
    top_cuisines = _get_cached_top_cuisines(mongo)
    return render_template(
        'index.html',
        featured_recipes_data=featured,
        cuisines=cuisines,
        top_cuisines=top_cuisines,
    )


@bp.route('/search', methods=['GET'])
@cache.cached(timeout=300, query_string=True, unless=lambda: current_user.is_authenticated)
def search():
    mongo = current_app.mongo

    time = 0
    dq_list = []
    include = ''
    exclude = ''
    sort = 'relevance'
    cuisine_filter = ''
    page = 1

    match = {}

    raw_time = request.args.get('time', '0')
    if raw_time and raw_time != '0':
        try:
            time = int(raw_time)
            match['total_time'] = {'$lte': time}
        except ValueError:
            pass

    dq_list = [d for d in request.args.getlist('dq') if d.strip()]
    if dq_list:
        match['dietary_requirements'] = {'$in': dq_list}

    if request.args.get('include'):
        include = request.args.get('include')
        match['ingredient_tags'] = {'$in': [i.strip() for i in include.split(',') if i.strip()]}

    if request.args.get('exclude'):
        exclude = request.args.get('exclude')
        excluded = [i.strip() for i in exclude.split(',') if i.strip()]
        match.setdefault('ingredient_tags', {})['$nin'] = excluded

    query_str = ''
    if request.args.get('q'):
        query_str = request.args.get('q').strip()
        if query_str:
            match['$text'] = {'$search': f'"{query_str}"'}

    if request.args.get('cuisine'):
        cuisine_filter = request.args.get('cuisine').strip()
        if cuisine_filter:
            match['cuisine'] = cuisine_filter

    if request.args.get('sort'):
        sort = request.args.get('sort')

    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    project_stage = [{'$project': _CARD_PROJECT}]
    match_stage = [{'$match': match}] if match else []

    # user_recipes: strip ingredient_tags filter (user_recipes use free-text ingredients, not tags)
    # and enforce status='approved' so only reviewed recipes surface.
    user_match = {k: v for k, v in match.items() if k != 'ingredient_tags'}
    user_match['status'] = 'approved'
    user_match_stage = [{'$match': user_match}]

    # Fetch all matching docs from all collections then sort and paginate in Python.
    # Per-collection DB pagination can never give a globally correct sort order when
    # the collections have different distributions of the sort field.
    bbc_all = list(mongo.db.bbcgoodfood.aggregate(match_stage + project_stage))
    tasty_all = list(mongo.db.tasty.aggregate(match_stage + project_stage))
    user_all = list(mongo.db.user_recipes.aggregate(user_match_stage + project_stage))
    data_all = bbc_all + tasty_all + user_all

    if sort == 'rating':
        data_all.sort(key=lambda d: float(d.get('average_rating') or 0), reverse=True)
    elif sort == 'popularity':
        data_all.sort(key=lambda d: int(d.get('number_of_ratings') or 0), reverse=True)
    elif sort == 'time':
        data_all.sort(key=lambda d: float(d.get('total_time') or float('inf')))
    elif sort == 'price':
        def _price_key(d):
            try:
                return float(d['prices'][1]['overall_cost_per_serving'])
            except (KeyError, IndexError, TypeError):
                return float('inf')
        data_all.sort(key=_price_key)

    total_pages = max(1, math.ceil(len(data_all) / PER_PAGE))
    page = min(page, total_pages)
    data = data_all[(page - 1) * PER_PAGE: page * PER_PAGE]

    return render_template(
        'recipes.html',
        data=data,
        query=query_str,
        time=time,
        dq=dq_list,
        include=include,
        exclude=exclude,
        sort=sort,
        cuisine=cuisine_filter,
        page=page,
        total_pages=total_pages,
    )


@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/terms')
def terms():
    return render_template('terms.html')


@bp.route('/privacy')
def privacy():
    return render_template('privacy.html')
