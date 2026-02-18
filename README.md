# Mallo

Lightweight Python web framework with a small core, built-in live reload, templates, routing, static files, and customizable error pages.

## Installation

Install from PyPI:

```bash
pip install mallo
```




## Quick Start

Create `app.py`:

```python
from mallo import Mallo

app = Mallo(__name__, live_reload=True)

@app.get('/')
def home(request):
    return '<h1>Hello from Mallo</h1>'

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
```

Run:

```bash
python app.py
```

Open `http://localhost:8000`.

---

## Hot Reload

Mallo has two reload-related behaviors:

1. `Server reload` (`use_reloader` in `app.run(...)`)
2. `Browser auto-refresh` (`live_reload` in `Mallo(...)`)

What the hot reloader does:

- Watches your project files for changes (`.py`, `.html`, `.css`, `.js`, and others).
- When a change is detected, it stops the running app process and starts a new one.
- In debug mode with `live_reload=True`, HTML responses include a small script that checks a reload endpoint.
- If the app process restarts, the browser detects a token change and refreshes automatically.

Enable both:

```python
app = Mallo(__name__, live_reload=True)
app.run(debug=True, use_reloader=True)
```

When hot reloader is deactivated:

```python
app = Mallo(__name__, live_reload=False)
app.run(debug=True, use_reloader=False)
```

What this means:

- `use_reloader=False`: Python process will not restart on file changes.
- `live_reload=False`: Browser auto-refresh script will not be injected.
- You need to restart the app manually after code changes.

---

## Template Rendering

Mallo supports 2 ways to render templates.

### 1) `render_template()` (from `templates/` folder)

Use when your templates live in a `templates` directory.

```python
from mallo import Mallo, render_template

app = Mallo(__name__)

@app.get('/')
def home(request):
    return render_template('index.html', name='Mallo')
```

Expected structure:

```text
project/
  app.py
  templates/
    index.html
```

You can change template folder:

```python
app = Mallo(__name__, template_folder='views')
```

### 2) `render_template_file()` (explicit file path)

Use when you want to render by full/relative file path directly.

```python
from mallo import Mallo, render_template_file

app = Mallo(__name__)

@app.get('/about')
def about(request):
    return render_template_file('pages/about.html', title='About')
```

### Template syntax

- Variables: `{{ name }}`
- Safe output (skip escaping): `{{ html_content | safe }}`
- If blocks: `{% if show %}...{% endif %}`
- For blocks: `{% for item in items %}...{% endfor %}`

---

## Routing

General route decorator:

```python
@app.route('/about')
def about(request):
    return 'About page'
```

`@app.route()` defaults to `GET`.

Route with multiple methods:

```python
@app.route('/contact', methods=['GET', 'POST'])
def contact(request):
    if request.method == 'POST':
        return 'Form submitted'
    return 'Contact form'
```

Method shortcuts:

```python
@app.get('/hello/<name>')
def hello(request, name):
    return f'Hello {name}'

@app.get('/user/<int:id>')
def user(request, id):
    return f'User #{id}'

@app.get('/file/<path:filepath>')
def file_route(request, filepath):
    return filepath
```

Generate routes by handler name:

```python
profile_url = app.url_for('user', id=10)  # /user/10
```

---

## Request Data

```python
@app.get('/search')
def search(request):
    q = request.get('q', '')
    return f'query={q}'

@app.post('/submit')
def submit(request):
    name = request.post('name', '')
    return f'name={name}'
```

JSON body:

```python
@app.post('/api')
def api(request):
    data = request.json or {}
    return {'received': data}
```

Multipart/form-data files:

```python
from mallo.response import Response

@app.post('/upload')
def upload(request):
    file_info = request.files.get('file')
    if not file_info:
        return Response('No file', status=400)
    return f"Uploaded: {file_info['filename']}"
```

---

## Responses

Return simple values:

- `str` -> HTML response
- `dict` / `list` -> JSON response with `application/json`

Or use response classes:

```python
from mallo.response import JSONResponse, RedirectResponse, FileResponse

@app.get('/json')
def json_route(request):
    return JSONResponse({'ok': True})

@app.get('/go')
def go(request):
    return RedirectResponse('/')
```

---

## Sessions and CSRF

Enable sessions by setting `secret_key`.

```python
app = Mallo(__name__, secret_key='change-this-in-production')
```

Use session:

```python
@app.get('/set')
def set_session(request):
    request.session['name'] = 'Betrand'
    return 'saved'
```

For unsafe methods (`POST`, `PUT`, `DELETE`), CSRF token is validated by default.
Include token in forms:

```python
@app.get('/form')
def form(request):
    return f"""
    <form method="post" action="/form">
      <input type="hidden" name="csrf_token" value="{request.csrf_token}">
      <input name="name">
      <button type="submit">Send</button>
    </form>
    """
```

Or send token in header `X-Csrf-Token`.

---

## Static Files

If `static/` exists, files are served at `/static/...`.

```text
project/
  static/
    styles.css
```

In HTML:

```html
<link rel="stylesheet" href="/static/styles.css">
```

---

## Error Pages (404/500)

Mallo ships with default styled error pages.

### Option 1: Configure custom error HTML files

```python
app = Mallo(
    __name__,
    error_page_404='templates/errors/404.html',
    error_page_500='templates/errors/500.html',
)
```

### Option 2: Register custom handlers

```python
from mallo import Mallo, render_template

app = Mallo(__name__)

@app.errorhandler(404)
def not_found(request):
    return render_template('errors/404.html')

@app.errorhandler(500)
def server_error(request):
    return render_template('errors/500.html')
```

Custom handler takes precedence over `error_page_404` / `error_page_500`.

---

## Request Hooks

```python
@app.before_request
def before(request):
    request.trace_id = 'abc123'

@app.after_request
def after(request, response):
    response.headers['X-Trace-Id'] = request.trace_id
    return response
```

---

## CLI

Create project:

```bash
mallo create myapp
```

Run with gunicorn (Linux/macOS):

```bash
mallo run app:app
```

Options:

```bash
mallo run app:app --host 0.0.0.0 --port 9000 --no-debug --no-reload
```

Notes:
- Defaults: host `localhost`, port `8000`, debug `on`.
- On Windows, `mallo run` prints a gunicorn support warning. Use `python app.py`.

---

## Minimal Full Example

```python
from mallo import Mallo, render_template

app = Mallo(__name__, secret_key='dev-secret', live_reload=True)

@app.get('/')
def home(request):
    return render_template('index.html', csrf_token=request.csrf_token, name='Mallo')

@app.post('/save')
def save(request):
    name = request.post('name', '')
    request.session['name'] = name
    return f'Saved: {name}'

@app.errorhandler(404)
def custom_404(request):
    return render_template('errors/404.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
```

---

## Contributing

Repository:

`https://github.com/Betrand-dev/mallo-fr.git`

Contributions are welcome for:
- testing coverage
- middleware improvements
- session backends
- template engine features
- documentation and examples
