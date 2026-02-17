**API Reference**

**Mallo**
Constructor:
1. `Mallo(import_name, static_url_path="/static", **config)`

Route registration:
1. `route(path, methods=None)`
1. `get(path)`
1. `post(path)`
1. `put(path)`
1. `delete(path)`
1. `url_for(handler_name, **kwargs)`

Template rendering:
1. `render_template(template_path, **context)`
1. Configure auto-escape with `Mallo(..., auto_escape=True)` and use `{{ value | safe }}` to bypass.

Server:
1. `run(host='localhost', port=8000, debug=False, use_reloader=True)`

WSGI entry:
1. `__call__(environ, start_response)`

**Request**
Attributes:
1. `method`
1. `path`
1. `headers`
1. `query`
1. `form`
1. `files`
1. `json`
1. `body`
1. `cookies`
1. `session` (only when `secret_key` is configured)
1. `csrf_token` (only when `secret_key` is configured)

Methods:
1. `get(key, default=None)`
1. `post(key, default=None)`
1. `is_xhr()`

**Response**
Constructor:
1. `Response(body='', status=200, headers=None, content_type='text/html')`

Methods:
1. `to_wsgi(start_response)`
1. `set_cookie(key, value='', max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False)`
1. `delete_cookie(key, path='/', domain=None)`

**JSONResponse**
Constructor:
1. `JSONResponse(data, status=200, headers=None)`

**RedirectResponse**
Constructor:
1. `RedirectResponse(location, status=302)`

**FileResponse**
Constructor:
1. `FileResponse(filepath, filename=None, status=200, headers=None)`

**CLI**
1. `mallo create <name>`
1. `mallo run` prints a message and does not execute your app
