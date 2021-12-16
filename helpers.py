import secret
import requests

DB_NAME = 'final_project.db'
API_KEY = secret.API_KEY
HEADERS = {'Authorization': 'Bearer {}'.format(API_KEY),
           'User-Agent': 'SI507 Final Project',
           'From': 'scottag@umich.edu'}
import json

def load_cache(cache_file_name):
    try:
        cache_file = open(cache_file_name, 'r')
        cached_stuff = cache_file.read()
        cache = json.loads(cached_stuff)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache, cache_file_name):
    cache_file = open(cache_file_name, 'w')
    stuff_write = json.dumps(cache)
    cache_file.write(stuff_write)
    cache_file.close()

CACHE_FILE = 'cache.json'
CACHE_DICT = load_cache(CACHE_FILE)


def make_url_request_using_cache(url_or_uniqkey, params=None):
    if url_or_uniqkey in CACHE_DICT.keys():
        print('Using cache')
        return CACHE_DICT[url_or_uniqkey]

    print('Fetching')
    if params == None:  # dictionary: url -> response.text
        response = requests.get(url_or_uniqkey, headers=HEADERS)
        CACHE_DICT[url_or_uniqkey] = response.text
    else:  # dictionary: uniqkey -> response.json()
        endpoint_url = 'https://api.yelp.com/v3/businesses/search'
        response = requests.get(endpoint_url, headers=HEADERS, params=params)
        CACHE_DICT[url_or_uniqkey] = response.json()

    save_cache(CACHE_DICT, CACHE_FILE)
    return CACHE_DICT[url_or_uniqkey]


def construct_unique_key(baseurl, params):
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')

    param_strings.sort()
    unique_key = baseurl + connector + connector.join(param_strings)
    return unique_key