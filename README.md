# SI507-FinalProject
## Overview
This project was completed in partial fulfillment of the requirments of SI 507 at the University of Michigan School of Information.
It retrieves state and business data (see below for detail) and employs SQLite, Flask, & Plotly to create an interactive website with basic visualizations of interest.
## Data
1) Selected data from the Census API--namely, the American Community Survey (ACS) for 2019 (the most recent avaialble).
https://api.census.gov/data/2019/acs/acs1/profile
2) Selected black-owned businesses accessed through the Yelp Fusion API
https://www.yelp.com/developers/documentation/v3/business_search
## Requirements
### Accessing the Yelp API
- An app must be registered through https://www.yelp.com/developers/documentation/v3/authentication
- A 'secret.py' file, containing you unique key, must be added to the directory from which you run the program.
  - Setting ```API_KEY = '(your secret key)'```
### Installing the necessary packages
- You will need requests, Flask, Jinja2, and plotly
  -  Simply run pip install (package) for each package
### Run the program
- From the command line:

```
python main.py
```

- Finally, head to http://localhost:5000/ to see the Flask application in action.
