import json
import math
import re
from datetime import datetime, timedelta
from urllib.parse import quote

import pycountry
import requests
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from extensions import cache

bp = Blueprint('stores', __name__, url_prefix='/api/stores')

# All ISO 3166-1 countries sorted by name, for the recipe page country dropdown
COUNTRIES = sorted(
    [(c.alpha_2.lower(), c.name) for c in pycountry.countries],
    key=lambda x: x[1],
)

STORE_TIER_MAP = {
    # UK budget
    'aldi': 'budget', 'lidl': 'budget', 'iceland': 'budget', 'asda': 'budget',
    # UK mid
    'tesco': 'mid', 'sainsbury': 'mid', 'morrisons': 'mid', 'co-op': 'mid', 'coop': 'mid',
    # UK premium
    'marks & spencer': 'premium', 'm&s': 'premium', 'waitrose': 'premium', 'whole foods': 'premium',
    # SG budget
    'sheng siong': 'budget', 'fairprice': 'budget', 'giant': 'budget',
    # SG mid
    'cold storage': 'mid', 'finest': 'mid',
    # SG premium
    'jason': 'premium', 'little farms': 'premium', 'hubers': 'premium',
    # Global budget
    'carrefour': 'budget', 'walmart': 'budget', 'penny': 'budget', 'netto': 'budget',
    'lidl': 'budget', 'aldi': 'budget',
    # Global mid
    'kroger': 'mid', 'trader joe': 'mid', 'countdown': 'mid', 'woolworths': 'mid',
    'coles': 'mid', 'spar': 'mid', 'pick n pay': 'mid', 'mercadona': 'mid',
    # Global premium
    'dean & deluca': 'premium', 'whole foods': 'premium',
}

# Map store name fragments to deep-link search URL templates
STORE_SEARCH_PATTERNS = {
    'tesco':        'https://www.tesco.com/groceries/en-GB/search?query={q}',
    'sainsbury':    'https://www.sainsburys.co.uk/gol-ui/search?query={q}',
    'asda':         'https://groceries.asda.com/search/{q}',
    'waitrose':     'https://www.waitrose.com/ecom/shop/browse/groceries?searchTerm={q}',
    'fairprice':    'https://www.fairprice.com.sg/search?query={q}',
    'cold storage': 'https://coldstorage.com.sg/search?q={q}',
    'woolworths':   'https://www.woolworths.com.au/shop/search/products?searchTerm={q}',
    'coles':        'https://www.coles.com.au/search?q={q}',
    'walmart':      'https://www.walmart.com/search?q={q}',
    'kroger':       'https://www.kroger.com/search?query={q}',
    '_default':     'https://www.google.com/search?tbm=shop&q={q}+{store}',
}

_TIMEOUT = 5

_UNITS = (
    r'kg|g|mg|ml|l|litre|liter|oz|lb|lbs|cup|cups|tbsp|tsp|'
    r'tablespoon|tablespoons|teaspoon|teaspoons|clove|cloves|'
    r'bunch|bunches|handful|handfuls|slice|slices|can|cans|tin|tins|'
    r'pack|packs|sprig|sprigs|pinch|dash|piece|pieces|head|heads|stalk|stalks'
)
_DESCRIPTORS = (
    r'large|medium|small|big|little|extra|fresh|freshly|dried|frozen|'
    r'canned|tinned|roughly|finely|thinly|coarsely|grated|chopped|sliced|'
    r'diced|minced|crushed|peeled|deseeded|halved|quartered|beaten|ground|'
    r'whole|ripe|soft|firm|lean|boneless|skinless|organic|heaped|level|rounded'
)


def _simplify_ingredient(ingredient: str) -> str:
    """Strip quantities, units, and trailing descriptors from an ingredient string.

    "1 lime, juiced"        → "lime"
    "200g dried pasta"      → "pasta"
    "2 cloves garlic"       → "garlic"
    "pinch of salt"         → "salt"
    "2 x 400g cans chopped tomatoes" → "tomatoes"
    """
    s = ingredient.split(',')[0].strip()  # drop ", juiced" etc.

    # Repeatedly strip leading quantity tokens (handles "2 x 400g cans …")
    for _ in range(5):
        prev = s
        s = re.sub(r'^(?:a|an)\s+', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'^[\d½⅓¼¾⅔⅛⅜⅝⅞/\-\.]+\s*', '', s).strip()
        s = re.sub(r'^x\s+', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(rf'^(?:{_UNITS})\b\s*', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'^of\s+', '', s, flags=re.IGNORECASE).strip()
        if s == prev:
            break

    # Strip leading descriptor adjectives (up to 3 deep, e.g. "large fresh whole")
    for _ in range(3):
        new_s = re.sub(rf'^(?:{_DESCRIPTORS})\s+', '', s, flags=re.IGNORECASE).strip()
        if new_s == s:
            break
        s = new_s

    result = s.strip().lower()
    return result if result else ingredient.lower()


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """Return distance in metres between two lat/lng points."""
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


_nominatim = Nominatim(user_agent='justcook-student/1.0', timeout=_TIMEOUT)
# Enforce Nominatim's 1 req/sec policy; retries once on transient errors
_nominatim_geocode = RateLimiter(
    _nominatim.geocode,
    min_delay_seconds=1,
    max_retries=1,
    error_wait_seconds=2,
    swallow_exceptions=True,
)

# Set of valid ISO 3166-1 alpha-2 codes (lowercase) for dropdown validation
_VALID_ISO2 = {c.alpha_2.lower() for c in pycountry.countries}

# Module-level geocode cache; satisfies Nominatim ToS (never repeat same query)
_geocode_cache: dict = {}


def _detect_postcode_country(postcode: str, location_hint: str = '') -> str:
    """Best-effort auto-detection when the user hasn't picked a country.

    Returns an ISO 3166-1 alpha-2 code (lowercase) or '' for unrestricted search.
    """
    p = postcode.upper().strip()
    hint = location_hint.lower()

    # UK: 1–2 letters then digit (SW1A, EC2A, GU21)
    if re.match(r'^[A-Z]{1,2}\d', p):
        return 'gb'

    # 6-digit numeric — disambiguate via profile location hint
    if re.match(r'^\d{6}$', p):
        if any(w in hint for w in ('singapore', 'singapura', ' sg', 'sg ')):
            return 'sg'
        if p[0] == '0':       # 01xxxx–09xxxx are exclusively Singapore sectors
            return 'sg'
        return ''             # ambiguous — unrestricted search

    return ''                 # unrestricted search


def _geocode_onemap(postcode: str):
    """OneMap fallback for Singapore postcodes absent from OSM.

    OSM/Nominatim coverage of SG postcodes is incomplete; OneMap is the
    Singapore government's authoritative source and fills that gap.
    This is not a per-country routing function — it is called only when
    Nominatim returns nothing for a SG-targeted query.
    """
    try:
        r = requests.get(
            'https://www.onemap.gov.sg/api/common/elastic/search',
            params={'searchVal': postcode, 'returnGeom': 'Y', 'getAddrDetails': 'N', 'pageNum': 1},
            timeout=_TIMEOUT,
        )
        if r.ok:
            results = r.json().get('results', [])
            if results:
                return float(results[0]['LATITUDE']), float(results[0]['LONGITUDE'])
    except Exception:
        pass
    return None


def _geocode_postcode(postcode: str, explicit_country: str = '', location_hint: str = ''):
    """Resolve any postcode to (lat, lng) using Nominatim via geopy.

    explicit_country: ISO 3166-1 alpha-2 code from the UI dropdown (e.g. 'gb', 'sg', 'us').
                      Empty string means auto-detect.
    location_hint:    user's free-text profile location for auto-detect fallback.
    """
    if explicit_country in _VALID_ISO2:
        iso2 = explicit_country
    else:
        iso2 = _detect_postcode_country(postcode, location_hint)  # '' = unrestricted

    cache_key = f'{postcode.upper()}|{iso2}'
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    try:
        loc = _nominatim_geocode(
            {'postalcode': postcode.replace(' ', '')},
            country_codes=iso2 if iso2 else None,
            exactly_one=True,
            addressdetails=False,
        )
        result = (loc.latitude, loc.longitude) if loc else None
    except Exception:
        result = None

    # Nominatim has incomplete Singapore postcode coverage; fall back to
    # OneMap (SG government API) when a SG-targeted query returns nothing.
    if result is None and iso2 == 'sg':
        result = _geocode_onemap(postcode)

    _geocode_cache[cache_key] = result
    return result


def _fetch_nearby_stores(lat: float, lng: float, api_key: str):
    try:
        r = requests.get(
            'https://api.geoapify.com/v2/places',
            params={
                'categories': 'commercial.supermarket',
                'filter': f'circle:{lng},{lat},5000',
                'limit': 20,
                'apiKey': api_key,
            },
            timeout=_TIMEOUT,
        )
        if r.ok:
            return r.json().get('features', [])
    except Exception:
        pass
    return None


def _map_tier(store_name: str) -> str:
    lower = store_name.lower()
    for fragment, tier in STORE_TIER_MAP.items():
        if fragment in lower:
            return tier
    return 'mid'


def _get_user_tier(max_budget_gbp) -> str:
    if max_budget_gbp is None:
        return 'mid'
    if float(max_budget_gbp) < 3:
        return 'budget'
    if float(max_budget_gbp) <= 6:
        return 'mid'
    return 'premium'


def _tier_score(store_tier: str, user_tier: str) -> int:
    order = ['budget', 'mid', 'premium']
    try:
        return abs(order.index(store_tier) - order.index(user_tier))
    except ValueError:
        return 1


def _build_maps_url(name: str, address: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote(f'{name} {address}')}"


def _build_search_url(store_name: str, ingredient: str) -> str:
    lower = store_name.lower()
    q = quote(ingredient)
    for fragment, pattern in STORE_SEARCH_PATTERNS.items():
        if fragment == '_default':
            continue
        if fragment in lower:
            return pattern.format(q=q)
    return STORE_SEARCH_PATTERNS['_default'].format(q=q, store=quote(store_name))


def _check_rate_limit(user_id, mongo):
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=1)
    doc = mongo.db.users.find_one({'_id': ObjectId(user_id)}, {'stores_api_calls': 1})
    recent = [t for t in (doc or {}).get('stores_api_calls', []) if t > cutoff]
    if len(recent) >= 10:
        retry_in = int((min(recent) + timedelta(hours=1) - now).total_seconds() / 60) + 1
        return False, retry_in
    recent.append(now)
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'stores_api_calls': recent}},
    )
    return True, 0


def _attach_search_urls(stores_raw: list, ingredients: list, user_tier: str) -> list:
    # Build simplified name → URL mapping once (same for every store, URL pattern differs per store)
    simplified = {}
    for ing in ingredients:
        key = _simplify_ingredient(ing)
        if key and key not in simplified:
            simplified[key] = key  # placeholder; URL added per store below
    result = []
    for store in stores_raw:
        search_urls = {key: _build_search_url(store['name'], key) for key in simplified}
        result.append({**store, 'search_urls': search_urls})
    return result


@bp.route('/nearby', methods=['GET'])
@login_required
def nearby():
    api_key = current_app.config.get('GEOAPIFY_API_KEY', '')
    mongo = current_app.mongo

    lat_raw = request.args.get('lat', '').strip()
    lng_raw = request.args.get('lng', '').strip()
    postcode = request.args.get('postcode', '').strip().upper()

    lat, lng = None, None

    if lat_raw and lng_raw:
        try:
            lat, lng = float(lat_raw), float(lng_raw)
        except ValueError:
            return jsonify({'error': 'bad_request', 'message': 'Invalid coordinates.'}), 400
    elif postcode:
        if not re.match(r'^[A-Z0-9 ]{3,10}$', postcode):
            return jsonify({'error': 'bad_request', 'message': 'Invalid postcode format.'}), 400
        explicit_country = request.args.get('country', '').strip().lower()
        if explicit_country not in _VALID_ISO2:
            explicit_country = ''
        user_loc_doc = mongo.db.users.find_one(
            {'_id': ObjectId(current_user.id)}, {'location': 1}
        )
        location_hint = (user_loc_doc or {}).get('location', '')
        coords = _geocode_postcode(postcode, explicit_country, location_hint)
        if coords is None:
            return jsonify({
                'error': 'bad_request',
                'message': 'Could not find that postcode. Please check and try again.',
            }), 400
        lat, lng = coords
    else:
        return jsonify({'error': 'bad_request', 'message': 'Provide lat/lng or a postcode.'}), 400

    raw_ingredients = request.args.get('ingredients', '[]')
    try:
        ingredients = json.loads(raw_ingredients)
        if not isinstance(ingredients, list):
            ingredients = []
    except (ValueError, TypeError):
        ingredients = []
    ingredients = [str(i) for i in ingredients[:30]]

    # Cache check — hits bypass rate limit entirely
    cache_key = f'stores_{round(lat, 2)}_{round(lng, 2)}'
    cached_stores = cache.get(cache_key)

    user_doc = mongo.db.users.find_one({'_id': ObjectId(current_user.id)}, {'max_budget_gbp': 1})
    user_tier = _get_user_tier((user_doc or {}).get('max_budget_gbp'))

    if cached_stores is not None:
        return jsonify({
            'stores': _attach_search_urls(cached_stores, ingredients, user_tier),
            'user_tier': user_tier,
            'cached': True,
        })

    # Rate limit — only for uncached calls
    allowed, retry_in = _check_rate_limit(current_user.id, mongo)
    if not allowed:
        suffix = 's' if retry_in != 1 else ''
        return jsonify({
            'error': 'limit_reached',
            'message': f"You've searched too many times this hour. Try again in {retry_in} minute{suffix}.",
            'retry_in_minutes': retry_in,
        })

    features = _fetch_nearby_stores(lat, lng, api_key)
    if features is None:
        return jsonify({
            'error': 'upstream_error',
            'message': 'Could not reach the store locator service. Please try again later.',
        }), 502

    stores_raw = []
    for feat in features:
        props = feat.get('properties', {})
        name = props.get('name', '').strip()
        if not name:
            continue
        address = ', '.join(
            p for p in [props.get('address_line1', ''), props.get('address_line2', '')] if p
        ).strip(', ')
        # Geoapify doesn't reliably populate properties.distance — compute from coordinates
        coords = feat.get('geometry', {}).get('coordinates', [lng, lat])
        store_lng, store_lat = float(coords[0]), float(coords[1])
        dist = _haversine_m(lat, lng, store_lat, store_lng)
        stores_raw.append({
            'name': name,
            'address': address,
            'distance_m': dist,
            'tier': _map_tier(name),
            'maps_url': _build_maps_url(name, address),
        })

    stores_raw.sort(key=lambda s: (_tier_score(s['tier'], user_tier), s['distance_m']))

    cache.set(cache_key, stores_raw, timeout=86400)

    return jsonify({
        'stores': _attach_search_urls(stores_raw, ingredients, user_tier),
        'user_tier': user_tier,
        'cached': False,
    })
