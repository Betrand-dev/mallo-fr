**Core Concepts**

**The Mallo App**
`Mallo` is the WSGI application. It:
1. Stores configuration and the router
1. Registers routes with decorators
1. Builds `Request` objects from WSGI environ
1. Returns `Response` objects to WSGI
1. Optionally injects a live-reload script in HTML responses
1. Runs a dev server using `wsgiref.simple_server`

Key methods:
1. `Mallo(__name__, static_url_path="/static", **config)`
1. `route(path, methods=None)`
1. `get(path)`, `post(path)`, `put(path)`, `delete(path)`
1. `render_template(template_path, **context)`
1. `run(host='localhost', port=8000, debug=False, use_reloader=True)`
1. `__call__(environ, start_response)` WSGI entry

**Routing**
The router converts path patterns into regex and matches them per HTTP method.

Supported patterns:
1. `/user/<name>` string param
1. `/user/<int:id>` integer param
1. `/price/<float:value>` float param
1. `/file/<path:filepath>` path param that can include slashes

How it works:
1. `add_route()` converts pattern to regex and stores it with method and handler
1. `match()` loops routes for a method, runs regex, and type-casts params
1. Returns `(handler, kwargs)` on match, otherwise `None`

Current limitation:
1. No route naming or reverse URL generation. `url_for()` is a stub.

**Request Object**
`Request` parses WSGI `environ` into a friendly API:
1. `method`, `path`, `query_string`
1. `headers` from `HTTP_*` and `CONTENT_*`
1. `query` parsed from `QUERY_STRING`, single values flattened
1. `body` raw bytes
1. `form` for `application/x-www-form-urlencoded`
1. `files` for `multipart/form-data`
1. `json` for `application/json`
1. `cookies`

Helpers:
1. `get(key, default=None)` query params
1. `post(key, default=None)` form params
1. `is_xhr()` checks `X-Requested-With` header

**Response Object**
`Response` stores:
1. `body` as string, bytes, dict, or list
1. `status` integer
1. `headers` dict

`to_wsgi(start_response)`:
1. Converts status to a string status line
1. Serializes dict/list to JSON
1. Encodes strings to bytes

Extra response classes:
1. `JSONResponse(data, status=200, headers=None)`
1. `RedirectResponse(location, status=302)`
1. `FileResponse(filepath, filename=None, status=200, headers=None)`

Cookie helpers:
1. `set_cookie(...)`
1. `delete_cookie(...)`

**Sessions and CSRF**
If you pass `secret_key` into `Mallo(...)`, sessions are enabled:
1. Session data is stored in memory, keyed by a signed cookie
1. A `csrf_token` is generated per session
1. For unsafe HTTP methods, CSRF tokens are required by default
1. Tokens can be sent as `X-Csrf-Token` header or `csrf_token` form field

**Templates**
Mallo uses a simple template engine:
1. Loads template files from a path
1. Caches templates unless `auto_reload=True`
1. Supports `{{ variable }}` substitution
1. Supports dot-notation for nested values
1. Supports simple `{% if %}` and `{% for %}` blocks
1. Auto-escapes HTML by default (use `{{ value | safe }}` to bypass)

Limitations:
1. No template inheritance

**Static Files**
If a `static` folder exists, Mallo automatically adds a route:
1. Default static URL is `/static`
1. Files are served from the `static` folder
1. MIME types are guessed from a small extension map

**Hot Reload**
Hot reload is optional and uses `watchdog`:
1. If `debug=True` and `use_reloader=True`, a `HotReloader` runs
1. It spawns a subprocess and restarts it on changes
1. It ignores common noisy folders like `.git` and `.venv`
1. It only watches files with certain extensions

Additionally, when `debug=True` and `live_reload=True`, the app injects a small script into HTML to auto-refresh the browser when reload tokens change.

**CLI**
The CLI supports:
1. `mallo create <name>` to scaffold a new project
1. `mallo run` is a placeholder and prints a message

**Utilities**
Includes small helpers:
1. `secure_filename()`
1. `generate_etag()`
1. `slugify()`
1. `camel_to_snake()` and `snake_to_camel()`
1. `parse_multipart_form()` is currently a stub
