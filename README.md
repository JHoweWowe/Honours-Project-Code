# Server Architecture
Server architecture design to be published soon
MongoDB - database used to store and retrieve data
PyMongo - Python library to integrate database and server
Server - Flask
Browser - HTML,CSS,JS,BootStrap (If time allows, use React for scability)

# Setup
1. Install MongoDB and MongoDBCompass - used to visualize data much more clearly
2. Open MongoDBCompass and connect it to localhost with port of 27017
3. Ensure Flask is setup properly
4. Execute `setup_settings.py` on console
5. Go to `settings.ini` and type in respective API and database settings
    - Database by default is called `db`
    - Collections can either be named `bbcgoodfood` or `tasty`

# Execute Script on University Server
1. Ensure MongoDB is running (in background)
2. Execute `python main.py`

# Heroku Deployment for Public Usage
NOTE: Figure how to deploy settings config file securely
1. Go to terminal
2. Obtain Heroku app name
3. Remove `settings.ini` from `.gitignore`
4. Execute `git push heroku master` on your terminal
5. Add `settings.ini` to `.gitignore`

# Web Scrapping
NOTE: Installation of Selenium and Google Chrome version is used for scraping data locally
Therefore it should ideally be done on a personal local machine.
1. Go to cmd and go to the `web_scraping` folder then type `python web_scrapping_module.py`

# Code Structure
Folders named `static` and `templates` where static files and templates are displayed

TODO:
Will be updated more later for report purposes