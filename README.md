# Overview
This project received an First Class equivalent grade. While there are minor issues, this was particularly one of my biggest accomplishments during my university journey and will continue to work on this project when free time allows.

# Server Architecture Design
![Honours Project Design Architecture](/honours_project_report/HonoursProjectDesignArchitectureUpdated.png)

* MongoDB - database used to store and retrieve unstructured data
* PyMongo - Python library to integrate database and server
* Server - Flask
* Browser - HTML,CSS,JS,BootStrap (If time allows, use React for scability)

For further details, please refer to the Honours Project report found in page 27 onwards.

# Local Development Setup
1. Install MongoDB and MongoDBCompass - used to visualize data much more clearly
2. Create a virtual environment in Python and activate it
    - `python -m venv venv`
3. Ensure the Python dependencies from `requirements.txt` are installed in the virtual environment, especially Flask
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
