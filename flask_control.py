from flask import Flask, request, render_template
from main import *
import requests

app = Flask(__name__)
@app.route('/')
def welcome():
    return render_template('table.html')

@app.route('/home/')
def test():
    figure1 = stateHisto()
    figure2 = avgRatingBlackPct()
    figure3 = avgRatingCategory()
    avg_rating = overallAvg()
    coolfig = curatedPlot1()
    return render_template('home.html', figure1=Markup(figure1), figure2=Markup(figure2),
                           figure3=Markup(figure3), coolfig=Markup(coolfig), avg_rating=avg_rating)

@app.route('/comparisons/', methods=["GET","POST"])
def form():
    state1=''
    state2=''
    variable=''
    if request.method == "POST":
        state1 = request.form.get("state1")
        state2 = request.form.get("state2")
        variable = request.form.get("variable")
    return render_template('nuance.html', state1=state1, state2=state2, variable=variable)

@app.route('/comparisons/<s1>/<s2>/<x>/', methods=["GET","POST"])
def plot(s1, s2, x):
    figure = betweenStates(s1, s2, x)
    url = '/comparisons/' + s1 + '/' + s2 + '/' + x + '/'
    category=''
    if request.method == "POST":
        category = request.form.get("addpath")
    url = url + category
    return render_template('comparison.html', figure=Markup(figure), s1=s1, s2=s2, url=url, x=x, category=category)

@app.route('/comparisons/<s1>/<s2>/<x>/<y>/')
def hey(s1, s2, x, y):
    figure = catBtwStates(s1, s2, x, y)
    url = '/comparisons/' + s1 + '/' + s2 + '/' + x + '/' + y +'/'
    return render_template('comparison.html', figure=Markup(figure), s1=s1, s2=s2, x=x,url=url)

@app.route('/recommender/<state>/', methods=["GET","POST"])
def histo(state):
    catpath = ''
    url = '/recommender/' + state + '/'
    figure = stateDistribution(state)
    note = 'Captain\'s Log: I wonder if the apparent preeminence of soul/southern food categories' \
           ' is reflective of true black business statistics, or if the Yelp Fusion search algorithm has' \
           ' some kind of bias.'
    if request.method == "POST":
        catpath = request.form.get("catpath")
    url = url + catpath
    return render_template('catstogram.html', figure=Markup(figure), state=state, note=note,
                           cat = catpath, url = url)

@app.route('/catrecommender/<category>/', methods=["GET","POST"])
def hista(category):
    figure = categoryDistribution(category)
    note = ''
    state = 'a'
    return render_template('catstogram.html', figure=Markup(figure), category=category,
                           state=state, note=note)

@app.route('/recommender/<state>/<category>/')
def recommendation(state, category):
    headers = ("Name","City","Rating","Reviews")
    results = recommender(state, category)
    return render_template('recommender.html', headers=headers, results=results,
                           category=category, state=state)

@app.route('/catrecommender/<category>/rec/')
def nationwidesearch(category):
    headers = ("Name", "City", "Rating", "Reviews")
    results = catrecommender(category=category)
    return render_template('catrecommender.html', headers=headers, results=results, category=category)

@app.route('/recommender/', methods=["GET","POST"])
def choose():
    state=None
    category=None
    if request.method == "POST":
        state = request.form.get("statepath")
        category = request.form.get("catpath")
    stateoptions = getJustStates()
    categoryoptions = getJustCategories()
    return render_template('choose.html', state=state, category=category,
                           stateoptions = stateoptions, categoryoptions=categoryoptions)

@app.route('/categories/')
def cats():
    categoryoptions = getJustCategories()
    return render_template('categories.html', categoryoptions=categoryoptions)