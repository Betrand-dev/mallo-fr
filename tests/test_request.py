import io

from mallo.request import Request


def make_environ(path='/', method='GET', query_string='', headers=None, body=b''):
    headers = headers or {}
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
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


def test_is_xhr_header():
    env = make_environ(headers={'X-Requested-With': 'XMLHttpRequest'})
    req = Request(env)
    assert req.is_xhr() is True


def test_multipart_form_and_file():
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="name"\r\n\r\n'
        'Mallo\r\n'
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="file"; filename="hello.txt"\r\n'
        'Content-Type: text/plain\r\n\r\n'
        'Hello file\r\n'
        f'--{boundary}--\r\n'
    ).encode()

    env = make_environ(
        method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
        body=body
    )
    req = Request(env)
    assert req.form.get('name') == 'Mallo'
    assert 'file' in req.files
    assert req.files['file']['filename'] == 'hello.txt'
    assert req.files['file']['content'] == b'Hello file'
