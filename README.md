**Mallo Framework**

Lightweight web framework with hot reload and a tiny core.

Docs index: `docs/index.md`

**Install (from source)**
```powershell
pip install -e .
```

**CLI**
```powershell
mallo create myapp
mallo run app:app
```

Note: Gunicorn is not supported on Windows. Use `python app.py` on Windows.
On Linux, install gunicorn:
```powershell
pip install gunicorn
```
