"""Unit tests for routes/stores.py — pure helpers and /api/stores/nearby endpoint."""
import json
from unittest.mock import patch

from routes.stores import (
    COUNTRIES,
    _VALID_ISO2,
    _build_maps_url,
    _build_search_url,
    _detect_postcode_country,
    _get_user_tier,
    _haversine_m,
    _map_tier,
    _simplify_ingredient,
    _tier_score,
)

# ---------------------------------------------------------------------------
# Sample Geoapify feature used in endpoint tests
# ---------------------------------------------------------------------------

_GEOAPIFY_FEATURE = {
    'type': 'Feature',
    'properties': {
        'name': 'Tesco Express',
        'address_line1': '12 High Street',
        'address_line2': 'London, EC1A',
    },
    'geometry': {'type': 'Point', 'coordinates': [-0.128, 51.508]},
}


# ===========================================================================
# COUNTRIES / _VALID_ISO2  (pycountry-generated constants)
# ===========================================================================

class TestCountriesConstant:
    def test_countries_is_non_empty_list(self):
        assert isinstance(COUNTRIES, list)
        assert len(COUNTRIES) > 100

    def test_countries_contains_gb(self):
        assert 'gb' in [c[0] for c in COUNTRIES]

    def test_countries_contains_sg(self):
        assert 'sg' in [c[0] for c in COUNTRIES]

    def test_countries_contains_us(self):
        assert 'us' in [c[0] for c in COUNTRIES]

    def test_countries_sorted_by_name(self):
        names = [c[1] for c in COUNTRIES]
        assert names == sorted(names)

    def test_countries_tuples_are_code_name_pairs(self):
        code, name = COUNTRIES[0]
        assert isinstance(code, str) and isinstance(name, str)
        assert len(code) == 2

    def test_valid_iso2_contains_gb(self):
        assert 'gb' in _VALID_ISO2

    def test_valid_iso2_contains_sg(self):
        assert 'sg' in _VALID_ISO2

    def test_valid_iso2_does_not_contain_uk(self):
        # 'uk' is not an ISO 3166-1 alpha-2 code — 'gb' is
        assert 'uk' not in _VALID_ISO2

    def test_valid_iso2_all_lowercase(self):
        assert all(c == c.lower() for c in _VALID_ISO2)


# ===========================================================================
# _simplify_ingredient
# ===========================================================================

class TestSimplifyIngredient:
    def test_strips_leading_quantity_and_comma_suffix(self):
        assert _simplify_ingredient('1 lime, juiced') == 'lime'

    def test_strips_grams_prefix(self):
        assert _simplify_ingredient('200g dried pasta') == 'pasta'

    def test_strips_cloves(self):
        assert _simplify_ingredient('2 cloves garlic') == 'garlic'

    def test_strips_pinch_of(self):
        assert _simplify_ingredient('pinch of salt') == 'salt'

    def test_strips_complex_multi_token(self):
        assert _simplify_ingredient('2 x 400g cans chopped tomatoes') == 'tomatoes'

    def test_returns_lowercase(self):
        result = _simplify_ingredient('3 large Chicken Breasts')
        assert result == result.lower()

    def test_plain_ingredient_unchanged(self):
        assert _simplify_ingredient('garlic') == 'garlic'

    def test_strips_a_prefix(self):
        assert _simplify_ingredient('a handful of spinach') == 'spinach'

    def test_strips_fresh_descriptor(self):
        assert _simplify_ingredient('fresh basil') == 'basil'

    def test_non_empty_fallback(self):
        # Weird edge case: should never return empty string
        result = _simplify_ingredient('1')
        assert result != ''


# ===========================================================================
# _haversine_m
# ===========================================================================

class TestHaversineM:
    def test_same_point_is_zero(self):
        assert _haversine_m(51.5, -0.1, 51.5, -0.1) == 0

    def test_known_distance_london_to_manchester(self):
        # London (51.507, -0.128) to Manchester (53.483, -2.244) ≈ 262 km
        dist = _haversine_m(51.507, -0.128, 53.483, -2.244)
        assert 260_000 < dist < 265_000

    def test_returns_integer(self):
        assert isinstance(_haversine_m(1.3, 103.8, 1.31, 103.81), int)

    def test_is_symmetrical(self):
        a = _haversine_m(51.5, -0.1, 51.6, -0.2)
        b = _haversine_m(51.6, -0.2, 51.5, -0.1)
        assert a == b

    def test_short_distance_in_metres(self):
        # Points ~111 m apart on same longitude
        dist = _haversine_m(51.500, -0.100, 51.501, -0.100)
        assert 100 < dist < 130


# ===========================================================================
# _detect_postcode_country
# ===========================================================================

class TestDetectPostcodeCountry:
    def test_uk_postcode_with_space_returns_gb(self):
        assert _detect_postcode_country('SW1A 1AA') == 'gb'

    def test_uk_postcode_without_space_returns_gb(self):
        assert _detect_postcode_country('EC2A4NE') == 'gb'

    def test_single_letter_uk_postcode_returns_gb(self):
        assert _detect_postcode_country('W1A 1AA') == 'gb'

    def test_sg_postcode_with_location_hint_returns_sg(self):
        assert _detect_postcode_country('238859', 'singapore') == 'sg'

    def test_sg_postcode_leading_zero_returns_sg(self):
        assert _detect_postcode_country('048622') == 'sg'

    def test_ambiguous_6digit_no_hint_returns_empty(self):
        # 500001 could be SG or elsewhere; no hint → let geocoder decide
        assert _detect_postcode_country('500001') == ''

    def test_us_zipcode_returns_empty(self):
        assert _detect_postcode_country('10001') == ''

    def test_5digit_us_zipcode_returns_empty(self):
        assert _detect_postcode_country('90210') == ''

    def test_unknown_format_returns_empty(self):
        assert _detect_postcode_country('XYZ123456') == ''


# ===========================================================================
# _map_tier
# ===========================================================================

class TestMapTier:
    def test_aldi_is_budget(self):
        assert _map_tier('Aldi') == 'budget'

    def test_lidl_is_budget(self):
        assert _map_tier('Lidl') == 'budget'

    def test_iceland_is_budget(self):
        assert _map_tier('Iceland Foods') == 'budget'

    def test_tesco_is_mid(self):
        assert _map_tier('Tesco Express') == 'mid'

    def test_sainsburys_is_mid(self):
        assert _map_tier("Sainsbury's Local") == 'mid'

    def test_morrisons_is_mid(self):
        assert _map_tier('Morrisons') == 'mid'

    def test_waitrose_is_premium(self):
        assert _map_tier('Waitrose & Partners') == 'premium'

    def test_whole_foods_is_premium(self):
        assert _map_tier('Whole Foods Market') == 'premium'

    def test_fairprice_is_budget(self):
        assert _map_tier('NTUC FairPrice') == 'budget'

    def test_cold_storage_is_mid(self):
        assert _map_tier('Cold Storage') == 'mid'

    def test_unknown_store_defaults_to_mid(self):
        assert _map_tier('Some Random Shop') == 'mid'

    def test_matching_is_case_insensitive(self):
        assert _map_tier('WAITROSE') == 'premium'
        assert _map_tier('aldi supermarkt') == 'budget'


# ===========================================================================
# _get_user_tier
# ===========================================================================

class TestGetUserTier:
    def test_none_defaults_to_mid(self):
        assert _get_user_tier(None) == 'mid'

    def test_below_3_is_budget(self):
        assert _get_user_tier(2.99) == 'budget'

    def test_exactly_3_is_mid(self):
        assert _get_user_tier(3.0) == 'mid'

    def test_between_3_and_6_is_mid(self):
        assert _get_user_tier(5.0) == 'mid'

    def test_exactly_6_is_mid(self):
        assert _get_user_tier(6.0) == 'mid'

    def test_above_6_is_premium(self):
        assert _get_user_tier(6.01) == 'premium'

    def test_string_value_coerced_correctly(self):
        assert _get_user_tier('2.50') == 'budget'
        assert _get_user_tier('7.00') == 'premium'


# ===========================================================================
# _tier_score
# ===========================================================================

class TestTierScore:
    def test_exact_match_is_zero(self):
        assert _tier_score('budget', 'budget') == 0
        assert _tier_score('mid', 'mid') == 0
        assert _tier_score('premium', 'premium') == 0

    def test_adjacent_tiers_score_one(self):
        assert _tier_score('budget', 'mid') == 1
        assert _tier_score('premium', 'mid') == 1
        assert _tier_score('mid', 'budget') == 1

    def test_opposite_ends_score_two(self):
        assert _tier_score('budget', 'premium') == 2
        assert _tier_score('premium', 'budget') == 2

    def test_unknown_store_tier_returns_one(self):
        assert _tier_score('unknown', 'mid') == 1


# ===========================================================================
# _build_maps_url
# ===========================================================================

class TestBuildMapsUrl:
    def test_starts_with_google_maps(self):
        url = _build_maps_url('Tesco', '12 High Street London')
        assert url.startswith('https://www.google.com/maps/search/')

    def test_contains_encoded_store_name(self):
        url = _build_maps_url('Aldi', '5 Main Road')
        assert 'Aldi' in url or '%41ldi' in url

    def test_no_literal_spaces_in_query(self):
        url = _build_maps_url('Waitrose', '1 King Street London')
        query_part = url.split('query=', 1)[-1]
        assert ' ' not in query_part


# ===========================================================================
# _build_search_url
# ===========================================================================

class TestBuildSearchUrl:
    def test_tesco_uses_tesco_domain(self):
        url = _build_search_url('Tesco Express', 'pasta')
        assert 'tesco.com' in url
        assert 'pasta' in url

    def test_sainsburys_uses_sainsburys_domain(self):
        url = _build_search_url("Sainsbury's Local", 'garlic')
        assert 'sainsburys.co.uk' in url

    def test_asda_uses_asda_domain(self):
        url = _build_search_url('Asda Superstore', 'milk')
        assert 'asda.com' in url

    def test_fairprice_uses_fairprice_domain(self):
        url = _build_search_url('NTUC FairPrice', 'rice')
        assert 'fairprice.com.sg' in url

    def test_cold_storage_uses_coldstorage_domain(self):
        url = _build_search_url('Cold Storage Finest', 'salmon')
        assert 'coldstorage.com.sg' in url

    def test_walmart_uses_walmart_domain(self):
        url = _build_search_url('Walmart Supercenter', 'eggs')
        assert 'walmart.com' in url

    def test_unknown_store_falls_back_to_google_shopping(self):
        url = _build_search_url('Random Corner Shop', 'tomatoes')
        assert 'google.com/search' in url
        assert 'tbm=shop' in url

    def test_ingredient_spaces_are_url_encoded(self):
        url = _build_search_url('Tesco', 'olive oil')
        assert ' ' not in url


# ===========================================================================
# /api/stores/nearby — authentication
# ===========================================================================

class TestNearbyAuth:
    def test_unauthenticated_request_is_not_200(self, client):
        resp = client.get('/api/stores/nearby?lat=51.5&lng=-0.1', follow_redirects=False)
        assert resp.status_code != 200

    def test_unauthenticated_request_redirects_to_login(self, client):
        resp = client.get('/api/stores/nearby?lat=51.5&lng=-0.1', follow_redirects=False)
        assert resp.status_code == 302
        location = resp.headers.get('Location', '')
        assert 'login' in location.lower() or 'auth' in location.lower()


# ===========================================================================
# /api/stores/nearby — bad request validation
# ===========================================================================

class TestNearbyBadRequest:
    def test_no_params_returns_400(self, logged_in_client):
        resp = logged_in_client.get('/api/stores/nearby')
        assert resp.status_code == 400
        assert json.loads(resp.data)['error'] == 'bad_request'

    def test_non_numeric_lat_returns_400(self, logged_in_client):
        resp = logged_in_client.get('/api/stores/nearby?lat=abc&lng=-0.1')
        assert resp.status_code == 400

    def test_non_numeric_lng_returns_400(self, logged_in_client):
        resp = logged_in_client.get('/api/stores/nearby?lat=51.5&lng=xyz')
        assert resp.status_code == 400

    def test_postcode_with_special_chars_returns_400(self, logged_in_client):
        resp = logged_in_client.get('/api/stores/nearby?postcode=!!!')
        assert resp.status_code == 400
        assert json.loads(resp.data)['error'] == 'bad_request'

    def test_postcode_too_long_returns_400(self, logged_in_client):
        resp = logged_in_client.get('/api/stores/nearby?postcode=ABCDEFGHIJK')
        assert resp.status_code == 400

    def test_postcode_too_short_returns_400(self, logged_in_client):
        resp = logged_in_client.get('/api/stores/nearby?postcode=AB')
        assert resp.status_code == 400


# ===========================================================================
# /api/stores/nearby — lat/lng path
# ===========================================================================

class TestNearbyLatLng:
    def test_returns_200_with_stores(self, logged_in_client):
        with patch('routes.stores._fetch_nearby_stores', return_value=[_GEOAPIFY_FEATURE]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.508&lng=-0.128')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'stores' in data
        assert 'user_tier' in data

    def test_store_object_has_required_fields(self, logged_in_client):
        with patch('routes.stores._fetch_nearby_stores', return_value=[_GEOAPIFY_FEATURE]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.508&lng=-0.128')
        store = json.loads(resp.data)['stores'][0]
        for field in ('name', 'address', 'distance_m', 'tier', 'maps_url', 'search_urls'):
            assert field in store, f'Missing field: {field}'

    def test_store_maps_url_is_google_maps(self, logged_in_client):
        with patch('routes.stores._fetch_nearby_stores', return_value=[_GEOAPIFY_FEATURE]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.508&lng=-0.128')
        store = json.loads(resp.data)['stores'][0]
        assert store['maps_url'].startswith('https://www.google.com/maps/')

    def test_geoapify_error_returns_502(self, logged_in_client):
        with patch('routes.stores._fetch_nearby_stores', return_value=None), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.508&lng=-0.128')
        assert resp.status_code == 502

    def test_no_stores_in_area_returns_empty_list(self, logged_in_client):
        with patch('routes.stores._fetch_nearby_stores', return_value=[]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.508&lng=-0.128')
        assert json.loads(resp.data)['stores'] == []

    def test_ingredients_produce_search_urls(self, logged_in_client):
        ingredients = json.dumps(['200g pasta', '2 cloves garlic'])
        with patch('routes.stores._fetch_nearby_stores', return_value=[_GEOAPIFY_FEATURE]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get(
                f'/api/stores/nearby?lat=51.508&lng=-0.128&ingredients={ingredients}'
            )
        store = json.loads(resp.data)['stores'][0]
        assert len(store['search_urls']) > 0

    def test_feature_without_name_is_skipped(self, logged_in_client):
        nameless = {**_GEOAPIFY_FEATURE, 'properties': {'address_line1': 'Some Road'}}
        with patch('routes.stores._fetch_nearby_stores', return_value=[nameless]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.508&lng=-0.128')
        assert json.loads(resp.data)['stores'] == []


# ===========================================================================
# /api/stores/nearby — postcode path
# ===========================================================================

class TestNearbyPostcode:
    def test_valid_postcode_geocoded_returns_200(self, logged_in_client):
        with patch('routes.stores._geocode_postcode', return_value=(51.508, -0.128)), \
             patch('routes.stores._fetch_nearby_stores', return_value=[_GEOAPIFY_FEATURE]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?postcode=EC2A4NE')
        assert resp.status_code == 200

    def test_unresolvable_postcode_returns_400(self, logged_in_client):
        with patch('routes.stores._geocode_postcode', return_value=None), \
             patch('routes.stores.cache.get', return_value=None):
            resp = logged_in_client.get('/api/stores/nearby?postcode=ZZ999ZZ')
        assert resp.status_code == 400
        assert json.loads(resp.data)['error'] == 'bad_request'

    def test_explicit_valid_country_code_accepted(self, logged_in_client):
        with patch('routes.stores._geocode_postcode', return_value=(40.71, -74.01)) as mock_gc, \
             patch('routes.stores._fetch_nearby_stores', return_value=[]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?postcode=10001&country=us')
        assert resp.status_code == 200
        # Confirm explicit country 'us' was forwarded to geocoder
        _, kwargs = mock_gc.call_args
        assert kwargs.get('explicit_country') == 'us' or mock_gc.call_args[0][1] == 'us'

    def test_invalid_country_code_treated_as_empty(self, logged_in_client):
        with patch('routes.stores._geocode_postcode', return_value=(51.5, -0.1)) as mock_gc, \
             patch('routes.stores._fetch_nearby_stores', return_value=[]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'):
            resp = logged_in_client.get('/api/stores/nearby?postcode=SW1A1AA&country=INVALID')
        assert resp.status_code == 200
        # 'INVALID' not in _VALID_ISO2, so explicit_country should be '' when passed
        call_explicit = mock_gc.call_args[0][1] if mock_gc.call_args[0] else mock_gc.call_args[1].get('explicit_country', '')
        assert call_explicit == ''


# ===========================================================================
# /api/stores/nearby — rate limiting and caching
# ===========================================================================

class TestNearbyRateLimitAndCache:
    def test_rate_limit_exceeded_returns_limit_reached_error(self, logged_in_client):
        with patch('routes.stores._check_rate_limit', return_value=(False, 12)), \
             patch('routes.stores.cache.get', return_value=None):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.5&lng=-0.1')
        data = json.loads(resp.data)
        assert data['error'] == 'limit_reached'
        assert 'retry_in_minutes' in data
        assert data['retry_in_minutes'] == 12

    def test_rate_limit_message_is_user_friendly(self, logged_in_client):
        with patch('routes.stores._check_rate_limit', return_value=(False, 5)), \
             patch('routes.stores.cache.get', return_value=None):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.5&lng=-0.1')
        assert b'5 minute' in resp.data

    def test_cached_response_skips_rate_limit(self, logged_in_client):
        cached = [{'name': 'Tesco', 'address': '', 'distance_m': 100, 'tier': 'mid', 'maps_url': ''}]
        with patch('routes.stores.cache.get', return_value=cached), \
             patch('routes.stores._check_rate_limit') as mock_rl:
            resp = logged_in_client.get('/api/stores/nearby?lat=51.5&lng=-0.1')
        assert resp.status_code == 200
        mock_rl.assert_not_called()

    def test_cached_response_sets_cached_true(self, logged_in_client):
        cached = [{'name': 'Lidl', 'address': '', 'distance_m': 200, 'tier': 'budget', 'maps_url': ''}]
        with patch('routes.stores.cache.get', return_value=cached):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.5&lng=-0.1')
        assert json.loads(resp.data)['cached'] is True

    def test_non_cached_response_sets_cached_false(self, logged_in_client):
        with patch('routes.stores._fetch_nearby_stores', return_value=[]), \
             patch('routes.stores.cache.get', return_value=None), \
             patch('routes.stores.cache.set'), \
             patch('routes.stores._check_rate_limit', return_value=(True, 0)):
            resp = logged_in_client.get('/api/stores/nearby?lat=51.5&lng=-0.1')
        assert json.loads(resp.data)['cached'] is False
