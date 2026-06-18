"""Unit tests for routes/main.py branches that require mocked DB interactions."""
from unittest.mock import patch


def test_text_search_returns_200(app, client):
    # $text aggregation is not supported in mongomock; patch both collections to return [].
    with patch.object(app.mongo.db.bbcgoodfood, 'aggregate', return_value=iter([])), \
         patch.object(app.mongo.db.tasty, 'aggregate', return_value=iter([])):
        resp = client.get('/search?q=pasta')
    assert resp.status_code == 200
