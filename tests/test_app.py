"""
Tests for Mallo application
"""

import io
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


def test_middleware_chain():
    app = Mallo(__name__)

    @app.middleware
    def add_header(request, call_next):
        response = call_next(request)
        if isinstance(response, Response):
            response.headers['X-Middleware'] = 'ok'
        return response

    @app.get('/hello')
    def hello(request):
        return 'hello'

    captured = {}

    def start_response(status, headers):
        captured['status'] = status
        captured['headers'] = dict(headers)

    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/hello',
        'QUERY_STRING': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': io.BytesIO(b''),
        'wsgi.errors': io.StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'CONTENT_LENGTH': '0',
    }

    body = b''.join(app(environ, start_response))
    assert captured['status'].startswith('200')
    assert captured['headers'].get('X-Middleware') == 'ok'
    assert body == b'hello'


def test_route_group_prefix_and_url_name():
    app = Mallo(__name__)
    api = app.group('/api', middleware=[])

    @api.get('/users/<int:id>', name='api_user')
    def user(request, id):
        return f'user-{id}'

    assert app.url_for('api_user', id=7) == '/api/users/7'


def test_env_override_template_folder(monkeypatch):
    monkeypatch.setenv('MALLO_TEMPLATE_FOLDER', 'views')
    app = Mallo(__name__)
    assert app.config_obj.get('template_folder') == 'views'
