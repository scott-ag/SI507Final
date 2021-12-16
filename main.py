import sqlite3
import csv
import pandas as pd
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import plot
import plotly.express as px
from flask import Flask, render_template, Markup
from us_state_abbrev import *
from flask_control import *
from helpers import *
from IPython.display import HTML
import statsmodels

#Classes#

class State:
    '''
    attr:
    -----
    id_pos: int
        state's index
    name: string
        the name of the state
    whitepct: float
        the percentage of the state's population designated 'white'
    blackpct: float
        the percentage of the state's population designated 'black',
        or two or more races where 'black' is one.
    diploma: float
        the percentage of the state's population, over the age of 25,
        who have a high school diploma or higher
    estincome: int
        the estimated median household income
    '''
    def __init__(self, id_pos=0, name=None,
                 whitepct=0, blackpct=0, diploma=0, estincome=0):
        self.id_pos = id_pos
        self.name = name
        self.whitepct = whitepct
        self.blackpct = blackpct
        self.diploma = diploma
        self.estincome = estincome

class Business:
    '''
    attr:
    -----
    name: string
        the business' name
    rating: float
        the business' Yelp rating from 1 to 5, with steps of 0.5
    price: float
        the business' price level from 1 to 3, with steps of 1
    category: string
        the business' category
    review_num: int
        the business' number of Yelp reviews
    city: string
        the city in which the business is located
    state: string
        the state in which the business is located
    '''
    def __init__(self, name=None, rating=0, price=None, category='', review_num=0, city='', state=''):
        self.name = name
        self.rating = rating
        self.price = price
        self.category = category
        self.review_num = review_num
        self.city = city
        self.state = state

#Create and fill the database#

def create_state_table():
    '''Connects to the database and creates a table/schema suited to the State class'''
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    states_sql = '''
        CREATE TABLE IF NOT EXISTS "State" (
        "Id" INTEGER PRIMARY KEY UNIQUE,
        "Name" VARCHAR(64) NOT NULL UNIQUE,
        "WhitePct" FLOAT NOT NULL,
        "BlackPct" FLOAT NOT NULL,
        "Diploma" FLOAT NOT NULL,
        "Income" INTEGER NOT NULL
        )
    '''
    cursor.execute(states_sql)
    conn.commit()
    conn.close()

def fill_state_table(state_objects):
    '''
    Connects to the database and inserts State objects
    Parameters
    ----------
    business_objects: a list of objects of the State class
    '''
    insert_state_sql = '''
    INSERT OR IGNORE INTO State
    VALUES (NULL,?,?,?,?,?)
    '''
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for s in state_objects:
        cursor.execute(insert_state_sql,
                       [s.name, s.whitepct, s.blackpct, s.diploma, s.estincome])
    conn.commit()
    conn.close()

def create_business_table():
    '''Connects to the database and creates a table/schema suited to the Business class'''
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    businesses_sql = '''
            CREATE TABLE IF NOT EXISTS "Business" (
            "Id" INTEGER NOT NULL PRIMARY KEY UNIQUE,
            "Name" VARCHAR(64) UNIQUE,
            "City" VARCHAR(64) NOT NULL,
            "State" VARCHAR(64) NOT NULL,
            "Rating" INTEGER,
            "Price" INTEGER,
            "Category" TEXT,
            "Num_Reviews" INTEGER
            )
        '''
    cursor.execute(businesses_sql)
    conn.commit()
    conn.close()

def fill_business_table(business_objects):
    '''
    Connects to the database and inserts State objects
    Parameters
    ----------
    business_objects: a list of objects of the State class
    '''
    insert_businesses_sql = '''
            INSERT OR REPLACE INTO Business
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
        '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for b in business_objects:
        cur.execute(insert_businesses_sql,
                    [b.name, b.city, b.state, b.rating, b.price, b.category,
                     b.review_num]
                    )

    conn.commit()
    conn.close()

def build_state():
    '''
    Gathers data from the Census API and returns it as a list of State objects
    Returns
    -------
    state_objects: A list of objects of the State class
    '''
    state_objects=[]
    endpoint_url = 'https://api.census.gov/data/2019/acs/acs1/profile?get=NAME,DP05_0037PE,DP05_0065PE,DP02_0067PE,DP03_0062E&for=state:*'
    results = requests.get(endpoint_url)
    results = results.json()
    for object in results:
        name = object[0]
        whitepct = object[1]
        blackpct = object[2]
        state = object[5]
        diploma = object[3]
        estincome = object[4]
        object = State(id_pos=state, name=name, whitepct=whitepct, blackpct=blackpct, diploma=diploma, estincome=estincome)
        state_objects.append(object)
    return state_objects


def build_business1(state_objects):
    '''Connects to the Yelp Fusion API and gathers data for each state in the list of
    State objects. This function gets results that are sorted by Yelp's Best Match
    parameter
    Parameters
    ----------
    state_objects: a list of objects of the State class
    Returns
    -------
    business_objects: a list of objects of the Business class
    '''
    business_objects = []
    endpoint_url = 'https://api.yelp.com/v3/businesses/search'
    for i in state_objects:
        params = {'location': i.name, 'term': 'black-owned', 'sort_by':'best_match','limit': 50}
        uniqkey = construct_unique_key(endpoint_url, params)
        results = make_url_request_using_cache(url_or_uniqkey=uniqkey, params=params)
        if 'businesses' in results.keys():
            for business in results['businesses']:
                rating = business['rating']
                try:
                    price = len(business['price'].strip())
                except:
                    price = None
                try:
                    category = business['categories'][0]['title']
                except:
                    category = ''
                city = business['location']['city']
                state = convertFromCode(business['location']['state'])
                review_num = business['review_count']
                name = business['name']
                object = Business(name=name, rating=rating, price=price, category=category,
                              review_num=review_num, city=city, state=state)
                business_objects.append(object)
    return business_objects


def build_business2(state_objects):
    '''
    Connects to the Yelp Fusion API and gathers data for each state in the list of
    State objects. This function gets results that are sorted by Yelp's Review Count
    parameter
    Parameters
    ----------
    state_objects: a list of objects of the State class
    Returns
    -------
    business_objects: a list of objects of the Business class
    '''
    business_objects = []
    endpoint_url = 'https://api.yelp.com/v3/businesses/search'
    for i in state_objects:
        params = {'location': i.name, 'term': 'black-owned', 'sort_by':'review_count','limit': 50}
        uniqkey = construct_unique_key(endpoint_url, params)
        results = make_url_request_using_cache(url_or_uniqkey=uniqkey, params=params)
        if 'businesses' in results.keys():
            for business in results['businesses']:
                rating = business['rating']
                try:
                    price = len(business['price'].strip())
                except:
                    price = None
                try:
                    category = business['categories'][0]['title']
                except:
                    category = ''
                city = business['location']['city']
                state = convertFromCode(business['location']['state'])
                review_num = business['review_count']
                name = business['name']
                object = Business(name=name, rating=rating, price=price, category=category,
                              review_num=review_num, city=city, state=state)
                business_objects.append(object)
    return business_objects


def build_database():
    '''Runs all of the previously defined object building and table creation/insertion
    functions, furnishing the database from which the rest of the program will operate'''
    print('Databasin')
    instances = build_state()
    create_state_table()
    fill_state_table(instances)
    businesses = build_business1(instances) + build_business2(instances)
    create_business_table()
    fill_business_table(businesses)
    print('Databas\'d')

#Retrieve the necessary data, then build the visualizations#

def search(query):
    '''
    Connects to the database and executes the SQL statement as defined
    in the building of the visualization
    Returns
    -------
    results
    '''
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    results = cursor.execute(query).fetchall()
    connection.close()
    return results


def flask_plot(xvals, yvals, title, fig_type, zvals=None, size=None):
    '''
    Builts a plotly graph_objects graph and returns it as a div for HTML display
    :param xvals: values for the x axis
    :param yvals: values for the y axis
    :param title: title to display above the graph
    :param fig_type: bar or scatter -- the manner in which to display the data
    :param zvals: optional z values
    :param size: optional size value for auto-adjusting marker sizes
    Returns
    -------
    fig_div: the div to be displayed in HTML
    '''
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": fig_type}]], subplot_titles=(title))
    if fig_type == 'scatter':
        if size:
            fig.add_trace(go.Scatter(x=xvals, y=yvals, mode='markers',
                                 marker=dict(color=zvals, opacity=0.3, size=[a/15 for a in size],
                                             line=dict(color='black', width=2))), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=xvals, y=yvals, mode='markers',
                                     marker=dict(color=zvals, opacity=0.5, size=8,
                                                 line=dict(color='black', width=2))), row=1, col=1)
    elif fig_type == 'bar':
        fig.add_trace(go.Bar(x=xvals, y=yvals, marker_color=zvals, marker=dict(opacity=0.5)), row=1, col=1)
#    elif fig_type == 'histogram':
#        fig.add_trace(go.Histogram(x=xvals), row=1, col=1)
    fig.update_layout(annotations=[dict(text=title, font_size=25, showarrow=False)],
                      paper_bgcolor='rgb(0,0,0,0)', plot_bgcolor='rgb(0,0,0,0)')
    fig_div = plot(fig, output_type="div")
    return fig_div

def overallAvg():
    '''Gets the overall average rating for all businesses'''
    query = '''SELECT ROUND(AVG(Rating), 2) FROM Business'''
    result = search(query)
    return result[0][0]

def stateHisto():
    '''Creates a histogram showing the prevalence of each state in the dataset'''
    query = '''SELECT State, COUNT(State) as ct from Business GROUP BY State 
    ORDER BY ct desc'''
    result = search(query)
    xvals = []
    yvals = []
    for row in result:
        xvals.append(row[0])
        yvals.append(row[1])
    title = 'Black-Owned Businesses By State (Dataset Description)'
    return flask_plot(xvals, yvals, title, 'bar')

def avgRatingBlackPct():
    '''Creates a scatter plot of the average Yelp rating for black businesses in each state,
    depending on the percentage of the population that's black.'''
    query = '''SELECT s.Name as state, s.BlackPct as PercentBlack, avg(b.Rating) as Rating FROM State s inner join Business b
    on s.Name = b.State GROUP BY state'''
    result = search(query)
    xvals=[]
    yvals=[]
    zvals=[]
    i = 0
    for row in result:
        i += 1
        xvals.append(row[1])
        yvals.append(row[2])
        zvals.append(i)
    title = 'Black Business Ratings vs. Black Population Percentage'
    return flask_plot(xvals, yvals, title, 'scatter', zvals)

def avgRatingCategory():
    '''Gets the average rating by category and displays it as a bar plot'''
    query = '''SELECT Category, avg(Rating) as Rating, Num_Reviews as Rating FROM Business 
    WHERE Num_Reviews >= 10 GROUP BY Category ORDER BY Rating desc'''
    result = search(query)
    xvals=[]
    yvals=[]
    zvals=[]
    for row in result[:5]:
        xvals.append(row[0])
        yvals.append(row[1])
        zvals.append('#17B137')
    for row in result[-5:]:
        xvals.append(row[0])
        yvals.append(row[1])
        zvals.append('#AB2318')
    title = 'Average Business Rating vs. Category (5 Great Examples, 5 Bad Ones)'
    return flask_plot(xvals, yvals, title, 'bar', zvals)


def betweenStates(state1, state2, yvar):
    '''
    Creates a bar plot showing the difference between two states for a single variable
    Parameters:
    state1: string
        the first state to compare
    state2: string
        the second state to compare
    yvar: string
        the variable to compare the states on
    '''
    statevars = ['WhitePct', 'BlackPct', 'Diploma', 'Income']
    busvars = ['Rating','Price','Num_Reviews']
    if yvar in statevars:
        query = '''SELECT s.Name as ident, {y} from State s LEFT OUTER JOIN Business b on s.Name = b.State
    WHERE (ident='{loc1}' AND {y} not like '%D%') OR (ident='{loc2}' AND {y} not like '%D%')
     GROUP BY ident'''.format(loc1=state1, loc2=state2, y=yvar)
    else:
        query = '''SELECT s.Name as ident, avg({y}) from State s LEFT OUTER JOIN Business b
        on s.Name = b.State WHERE (s.Name = '{loc1}' OR s.Name = '{loc2}')
        GROUP BY ident'''.format(y=yvar, loc1=state1, loc2=state2)
    result = search(query)
    xvals = []
    yvals = []
    zvals = []
    for row in result:
        xvals.append(row[0])
        yvals.append(row[1])
        if row[0] == state1:
            zvals.append('white')
        elif row[0] == state2:
            zvals.append('black')
    title = '{y} ({loc1} vs. {loc2})'.format(loc1=state1, loc2=state2, y=yvar)
    return flask_plot(xvals, yvals, title, 'bar', zvals)

def catBtwStates(s1, s2, x, y):
    '''
    Creates a bar plot showing the difference between two states for a single variable,
    narrowed to a certain category.
    Parameters
    ----------
    s1: string
        The first state to compare
    s2: string
        The second state to compare
    x: string
        The variable on which to compare the two states
    y: string
        The category on which to narrow in
    '''
    query = '''SELECT s.Name as ident, avg({x}) FROM State s LEFT OUTER JOIN Business b on s.Name = b.State
    WHERE Category = '{y}' AND (ident='{s1}' OR ident='{s2}')
     GROUP BY ident'''.format(x=x, y=y, s1=s1, s2=s2)
    result = search(query)
    xvals = []
    yvals = []
    zvals = []
    for row in result:
        xvals.append(row[0])
        yvals.append(row[1])
        if row[0] == s1:
            zvals.append('white')
        else:
            zvals.append('black')
    title = '{x} for {y} Businesses ({loc1} vs. {loc2})'.format(y=y, x=x, loc1=s1, loc2=s2)
    return flask_plot(xvals, yvals, title, 'bar', zvals)

def curatedPlot1():
    '''
    Creates a scatter plot of business ratings versus population's percent black,
    adjusting market size to reflect the number of reviews
    '''
    query='''SELECT s.Name as identity, s.BlackPct, b.Rating, b.Num_Reviews FROM
    State s INNER JOIN Business b ORDER BY RANDOM() LIMIT 50'''
    result = search(query)
    xvals = []
    yvals = []
    zvals = []
    test = []
    i = 0
    for row in result:
        xvals.append(row[1])
        yvals.append(row[2])
        test.append(row[3])
        i += 1
        zvals.append(i)
    title = 'Business Rating vs. State\'s Percent Black (Size = # Reviews)'
    return flask_plot(xvals, yvals, title, 'scatter', zvals=zvals, size=test)

def stateDistribution(state):
    '''
    Generates a bar plot/histogram showing the distribution of categories for
    a given state
    Parameters
    ----------
    state: string
        the state for which to generate the category distribution
    '''
    query = '''SELECT Category, COUNT(Category) as ct FROM Business
    WHERE State = '{state}' GROUP BY Category ORDER BY ct desc'''.format(state=state)
    result = search(query)
    xvals = []
    yvals = []
    for row in result:
        xvals.append(row[0])
        yvals.append(row[1])
    title = 'Count by Category for {state}'.format(state=state)
    return flask_plot(xvals, yvals, title, 'bar')

def categoryDistribution(category):
    '''
    Generates a bar plot/histogram showing the distribution of states for
    a given category
    Parameters
    ----------
    category: string
        the category for which to generate the cstate distribution
    '''
    query = '''SELECT State, COUNT(Category) as ct FROM Business
    WHERE Category = '{category}' GROUP BY State ORDER BY ct desc'''.format(category=category)
    result = search(query)
    xvals = []
    yvals = []
    for row in result:
        xvals.append(row[0])
        yvals.append(row[1])
    title = '{cat} Businesses by State'.format(cat=category)
    return flask_plot(xvals, yvals, title, 'bar')


def recommender(state='Michigan', category='Chicken Wings', minreviews=10):
    '''
    Generates a table with recommendations based on user preferences for
    state and category (limiting to 10 results, and to businesses with more than 10
    reviews)
    Parameters
    -----------
    state: string
        The state in which to generate recommendations
    category: string
        The category in which to generate recommendations
    minreviews: int
        default at 10, the minimum number of reviews required for a business
        to show up in the recommendations
    Returns
    ------
    table: A table with business names, city, rating, and the number of reviews
    '''
    query = '''SELECT DISTINCT Name, City, Rating, Num_Reviews FROM Business
    WHERE State = '{state}' AND Category = '{category}' AND Num_Reviews >= {minreviews} 
    ORDER BY Rating desc LIMIT 10'''.format(state=state, category=category, minreviews=minreviews)
    table = search(query)
    return table

def catrecommender(category, minreviews=10):
    '''
    Generates a table with recommendations based on user preference for catergory
    (nationwide search)
    Parameters
    ----------
    category: string
        The category in which to search for recommendations
    minreviews: int
        default at 10, the minimum number of reviews required for a business
        to show up in the recommendations
    Returns
    -------
    table: A table with business names, city, rating, and the number of reviews
    '''
    query = '''SELECT DISTINCT Name, City, Rating, Num_Reviews FROM Business 
    WHERE Category = '{category}' AND Num_Reviews >= {minreviews} 
    ORDER BY Rating desc LIMIT 10'''.format(category=category, minreviews=minreviews)
    table = search(query)
    return table

def getJustStates():
    '''Gets the list of states for display/reference'''
    query = '''SELECT DISTINCT Name from State'''
    result = search(query)
    return result

def getJustCategories():
    '''Gets the list of categories for display/reference'''
    query = '''SELECT DISTINCT Category from Business'''
    result = search(query)
    return result


if __name__ == '__main__':
    build_database()

    app.run(debug=True)

