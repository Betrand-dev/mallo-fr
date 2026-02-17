"""
Tests for Mallo application
"""

import pytest
from mallo import Mallo, Request, Response


def test_app_creation():
    """Test basic app creation"""
    app = Mallo(__name__)
    assert app.import_name == __name__
    assert app.router is not None


def test_route_decorator():
    """Test route registration"""
    app = Mallo(__name__)

    @app.route('/')
    def home(request):
        return 'Home'

    matching = [route for route in app.router.routes if route['original_path'] == '/']
    assert len(matching) == 1
    assert matching[0]['method'] == 'GET'


def test_dynamic_route():
    """Test dynamic route matching"""
    app = Mallo(__name__)

    @app.route('/user/<int:id>')
    def user(request, id):
        return f'User {id}'

    match = app.router.match('/user/123', 'GET')
    assert match is not None
    handler, kwargs = match
    assert kwargs == {'id': 123}


def test_response_json_content_type():
    response = Response({'a': 1})
    captured = {}

    def start_response(status, headers):
        captured['status'] = status
        captured['headers'] = dict(headers)

    body = b''.join(response.to_wsgi(start_response))
    assert captured['headers'].get('Content-Type') == 'application/json'
    assert body == b'{"a": 1}'
