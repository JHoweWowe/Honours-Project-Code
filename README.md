# Overview
This project received an First Class equivalent grade. While there are minor issues, this was particularly one of my biggest accomplishments during my university journey and will continue to work on this project when free time allows.

# Server Architecture Design
![Honours Project Design Architecture](/honours_project_report/HonoursProjectDesignArchitectureUpdated.png)

* MongoDB - database used to store and retrieve unstructured data
* PyMongo - Python library to integrate database and server
* Server - Flask
* Browser - HTML,CSS,JS,BootStrap (If time allows, use React for scability)
* Cloud - Heroku

For further details, please refer to the Honours Project report found in page 27 onwards.

# Local Development + Setup + Deployment
1. Install MongoDB and MongoDBCompass - used to visualize data much more clearly
2. Create a virtual environment in Python and activate it
    - `python -m venv venv`
3. Ensure the Python dependencies from `requirements.txt` are installed in the virtual environment, especially Flask
    - `pip install -r requirements.txt`
4. Execute `setup_settings.py` on console
5. Go to `settings.ini` and type in respective API and database settings
    - Database by default is called `db`
    - Collections can either be named `bbcgoodfood` or `tasty`.
6. Run MongoDB in your local environment and connect it to localhost with port of 27017 (or MongoDBCloud database - lowest tier is free as of Feb 2023)
7. Run `main.py` - this deploys the Flask server only for **local** development and not production usage.

# Code Structure
Folders named `static` and `templates` where static files and templates are respectively displayed.
`web_scraping` folder contains the Python files required to scrape the website.
`honours_project_report` folder contains the Honours Project report and images.
`tests/` folder contains the automated test suite (see **Running Tests** below).

# Web Scrapping
NOTE: Installation of Selenium and Google Chrome version is used for scraping data locally on the database. This is done separately from deploying onto Heroku. It should ideally be done on a personal local machine.
Configurable deployable websites include BBCGoodFood and Tasty. BBCGoodFood collections are supported such as *https://www.bbcgoodfood.com/recipes/collection/february-recipes*
Tasty website has more flexibility where base url is configured as *https://tasty.co/search*
The `base_url` of the website to scrape can be configured in the `settings.ini` file

1. Simply run the respective Python website module. Go to cmd and go to the `web_scraping` folder then type `python web_scrapping_module.py`
2. Ensure the recipes are stored in the MongoDB collections

# Heroku Deployment for Public Usage
NOTE: Figure how to deploy settings config file securely
1. Go to terminal
2. Create and obtain the Heroku app name on *heroku.com*, after this then follow instructions given
3. Remove `settings.ini` from `.gitignore`
4. Check in `requirements.txt` file to ensure Python dependencies are installed
5. Execute `git push heroku master` on your terminal
6. Add `settings.ini` to `.gitignore`

Heroku Configuration Setup Before Deploying:
heroku config:set FOOD_RECIPE_DATABASE_USERNAME=your_username
  FOOD_RECIPE_DATABASE_PASSWORD=your_password FOOD_RECIPE_DATABASE_HOSTNAME=your_hostname -a
  <your-app-name>

# Running Tests

The project uses [pytest-bdd](https://pytest-bdd.readthedocs.io/) (Gherkin/BDD style) with [mongomock](https://github.com/mongomock/mongomock) so **no live MongoDB connection or environment variables are required**.

### Install test dependencies
```bash
pip install -r requirements.txt # Dependencies required for main app to run
pip install -r requirements-test.txt
```

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run with coverage report
```bash
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

### Test structure
```
tests/
├── conftest.py              # App fixture (mongomock), seed data, shared step definitions
├── features/
│   ├── homepage.feature     # Homepage load, featured recipes, cuisine browser
│   ├── search.feature       # Filters: cuisine, dietary, time, sort, empty state
│   ├── recipe_detail.feature# Title, ingredients, directions, price, related recipes
│   └── time_converter.feature # Unit tests for the scraper time-string parser
└── step_defs/
    ├── test_homepage_steps.py
    ├── test_search_steps.py
    ├── test_recipe_detail_steps.py
    └── test_time_converter_steps.py
```

CI runs automatically on every push and pull request to `master` via GitHub Actions (`.github/workflows/ci.yml`).

# Raising PR for changes
1. Run the automated test suite and confirm all tests pass:
    ```bash
    python -m pytest tests/ -v
    ```
2. Conduct manual smoke tests in your local environment:
    - Test search pagination: verify prev/next buttons work and results are consistent.
    - Test pricing sort: search any term, sort by price, confirm ascending order.
    - Test on mobile (Chrome DevTools) after each UI change to check responsive layout.
3. Raise the PR to master from your feature branch