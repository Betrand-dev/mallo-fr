**Getting Started**

**Overview**
Mallo is a lightweight Python web framework with a minimal WSGI core, a small router, a simple request/response model, basic template rendering, and optional hot reload for development. It is designed to be easy to understand and extend rather than feature-complete.

**Install**
```powershell
pip install -r requirements.txt
```

**Create Your First App**
```python
from mallo import Mallo

app = Mallo(__name__, live_reload=True)

@app.route('/')
def home(request):
    return '<h1>Hello, Mallo!</h1>'

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
```

**Run It**
```powershell
python app.py
```

**CLI (Gunicorn)**
```powershell
mallo run app:app
mallo run app:app --host 0.0.0.0 --port 8000 --no-debug
```

Note: Gunicorn is not supported on Windows. Use `python app.py` on Windows or run the CLI on Linux.

**Project Layout**
In this repository:
1. `mallo/` core framework package
1. `tests/` tests (minimal coverage today)
1. `templates/` and `static/` are used by the example app

In your own app:
1. `templates/` holds HTML templates
1. `static/` holds CSS, JS, images
1. `app.py` (or any script) creates and runs the `Mallo` instance
