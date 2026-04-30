import configparser
import os

from flask import Flask
from pymongo import MongoClient, TEXT

from extensions import cache

# Load .env if python-dotenv is available (falls back to settings.ini)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_mongo_uri():
    cfg = configparser.ConfigParser()
    cfg.read('settings.ini')

    def env_or_cfg(section, key):
        return os.environ.get(f'{section.upper()}_{key.upper()}') or cfg.get(section, key, fallback='')

    username = env_or_cfg('food_recipe_database', 'username')
    password = env_or_cfg('food_recipe_database', 'password')
    hostname = env_or_cfg('food_recipe_database', 'hostname')
    return f'mongodb+srv://{username}:{password}@{hostname}/db?retryWrites=true&w=majority'


def create_app():
    app = Flask(__name__, static_url_path='', static_folder='static')

    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)

    mongo = MongoClient(_get_mongo_uri())
    mongo.db.bbcgoodfood.create_index(
        [('title', TEXT), ('description', TEXT)], default_language='english'
    )
    mongo.db.tasty.create_index(
        [('title', TEXT), ('description', TEXT)], default_language='english'
    )
    app.mongo = mongo

    from routes.main import bp as main_bp
    from routes.recipes import bp as recipes_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(recipes_bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
