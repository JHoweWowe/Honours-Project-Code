import math

from flask import Blueprint, render_template, request, current_app
from extensions import cache

bp = Blueprint('main', __name__)

PER_PAGE = 6


@bp.route('/', methods=['GET'])
@cache.cached(timeout=300, key_prefix='index')
def index():
    mongo = current_app.mongo
    featured = list(
        mongo.db.bbcgoodfood
        .find({'average_rating': {'$gt': 4.4, '$lt': 5}})
        .sort('number_of_ratings', -1)
        .limit(3)
    )
    raw_cuisines = mongo.db.bbcgoodfood.distinct('cuisine') + mongo.db.tasty.distinct('cuisine')
    cuisines = sorted({c for c in raw_cuisines if c and c.strip()})
    return render_template('index.html', featured_recipes_data=featured, cuisines=cuisines)


@bp.route('/search', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
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

    match_stage = [{'$match': match}] if match else []

    # Fetch all matching docs from both collections then sort and paginate in Python.
    # Per-collection DB pagination can never give a globally correct sort order when
    # the two collections have different distributions of the sort field.
    bbc_all = list(mongo.db.bbcgoodfood.aggregate(match_stage))
    tasty_all = list(mongo.db.tasty.aggregate(match_stage))
    data_all = bbc_all + tasty_all

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
