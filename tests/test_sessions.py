import io

from mallo import Mallo


def make_environ(path='/', method='GET', headers=None, body=b''):
    headers = headers or {}
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': io.BytesIO(body),
        'wsgi.errors': io.StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'CONTENT_LENGTH': str(len(body)),
    }

    for key, value in headers.items():
        normalized = key.upper().replace('-', '_')
        if normalized in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[normalized] = value
        else:
            environ[f'HTTP_{normalized}'] = value
    return environ


def call_app(app, environ):
    captured = {}

    def start_response(status, headers):
        captured['status'] = status
        captured['headers'] = dict(headers)

    body = b''.join(app(environ, start_response))
    return captured['status'], captured['headers'], body


def test_sessions_and_csrf():
    app = Mallo(__name__, secret_key='test-secret')

    @app.get('/form')
    def form(request):
        return 'ok'

    @app.post('/submit')
    def submit(request):
        return 'done'

    status, headers, body = call_app(app, make_environ('/form', 'GET'))
    assert status.startswith('200')
    assert 'Set-Cookie' in headers
    cookie_value = headers['Set-Cookie'].split(';', 1)[0].split('=', 1)[1].strip()
    session_id = cookie_value.split('|', 1)[0]
    csrf_token = app._session_store[session_id]['csrf_token']

    post_body = f'csrf_token={csrf_token}'.encode()
    status, headers, body = call_app(app, make_environ(
        '/submit',
        'POST',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': f'mallo_session={cookie_value}',
        },
        body=post_body
    ))
    assert status.startswith('200')

    status, headers, body = call_app(app, make_environ(
        '/submit',
        'POST',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': f'mallo_session={cookie_value}',
        },
        body=b''
    ))
    assert status.startswith('403')
