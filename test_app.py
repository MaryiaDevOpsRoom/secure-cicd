import pytest
from app import app as flask_app
from unittest.mock import patch

# A dummy cat picture URL for mocking
FAKE_CAT_URL = "https://fakecat.com/image.jpg"


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


@patch('app.get_random_cat_picture', return_value=FAKE_CAT_URL)
@patch('app.url_collection')
def test_shorten_url(mock_collection, mock_cat, client):
    """Test shortening a valid URL with no custom alias"""
    mock_collection.find_one.return_value = None
    response = client.post('/shorten', data={'url': 'https://example.com'})
    assert response.status_code == 200
    assert b'shortcode' in response.data or b'Alias already taken' not in response.data


@patch('app.get_random_cat_picture', return_value=FAKE_CAT_URL)
@patch('app.url_collection')
def test_custom_alias_taken(mock_collection, mock_cat, client):
    """Test submitting a custom alias that already exists"""
    mock_collection.find_one.return_value = {'alias': 'custom123'}
    response = client.post('/shorten', data={'url': 'https://example.com', 'alias': 'custom123'})
    assert b'Alias already taken' in response.data


@patch('app.get_random_cat_picture', return_value=FAKE_CAT_URL)
@patch('app.url_collection')
def test_custom_alias_success(mock_collection, mock_cat, client):
    """Test successful custom alias creation"""
    mock_collection.find_one.return_value = None
    response = client.post('/shorten', data={'url': 'https://example.com', 'alias': 'myalias'})
    assert b'myalias' in response.data


@patch('app.url_collection')
def test_redirect_success(mock_collection, client):
    """Test redirection from a valid shortcode"""
    mock_collection.find_one.return_value = {'url': 'https://example.com'}
    response = client.get('/myalias')
    assert response.status_code == 302
    assert response.location == 'https://example.com'


@patch('app.url_collection')
def test_redirect_not_found(mock_collection, client):
    """Test redirecting with an invalid shortcode"""
    mock_collection.find_one.return_value = None
    response = client.get('/invalidcode')
    assert response.status_code == 200  # Rendering 404 template
    assert b'404' in response.data or b'not found' in response.data.lower()