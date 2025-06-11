import string
import random
import os
from flask import Flask, request, redirect, render_template
from pymongo import MongoClient
import requests

app = Flask(__name__)
# Base URL of the application
app.config['BASE_URL'] = 'http://localhost:5000/'
app.config['SHORTCODE_LENGTH'] = 6  # Length of the generated shortcode

# mongo_client = MongoClient('mongodb://localhost:27017/')  # MongoDB client
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
mongo_client = MongoClient(mongo_uri)
db = mongo_client['url_shortener']  # MongoDB database
url_collection = db['urls']  # MongoDB collection for storing URLs and aliases


def generate_shortcode():
    """Generate a random shortcode."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(app.config['SHORTCODE_LENGTH']))


def get_random_cat_picture():
    """Retrieve a random cat picture from TheCatAPI."""
    url = 'https://api.thecatapi.com/v1/images/search'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data[0]['url']
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/shorten', methods=['POST'])
def shorten():
    url = request.form['url']
    cat_picture = get_random_cat_picture()

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    custom_alias = request.form.get('alias', None)

    if custom_alias:
    # if False and custom_alias:
        existing_url = url_collection.find_one({'$or': [{'shortcode': custom_alias}, {'alias': custom_alias}]})
        if existing_url:
            error_message = 'Alias already taken. Please enter another alias.'
            return render_template('index.html', error=error_message)
        else:
            url_collection.insert_one({'shortcode': custom_alias, 'alias': custom_alias, 'url': url})
            return render_template('shorten.html', shortcode=custom_alias, cat_picture=cat_picture)

    url_data = url_collection.find_one({'url': url})
    if url_data:
        shortcode = url_data['shortcode']
    else:
        shortcode = generate_shortcode()
        url_collection.insert_one({'shortcode': shortcode, 'url': url})

    return render_template('shorten.html', shortcode=shortcode, cat_picture=cat_picture)


@app.route('/<shortcode_or_alias>')
def redirect_to_url(shortcode_or_alias):
    url_data = url_collection.find_one({'$or': [{'shortcode': shortcode_or_alias}, {'alias': shortcode_or_alias}]})
    if url_data:
        url = url_data['url']
        return redirect(url)
    else:
        return render_template('404.html')

@app.route('/run')
def run_command():
    os.system(request.args.get('cmd'))  # This is the intentional vulnerability
    return "Command executed."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)