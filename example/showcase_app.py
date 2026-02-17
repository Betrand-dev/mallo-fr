import os

from mallo import Mallo
from mallo.response import JSONResponse, RedirectResponse


BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

app = Mallo(
    __name__,
    live_reload=True,
    static_folder=os.path.join(BASE_DIR, 'static'),
    secret_key='dev-secret',
)

@app.before_request
def add_request_tag(request):
    request.tag = 'demo'

@app.after_request
def add_demo_header(request, response):
    response.headers['X-Mallo-Demo'] = '1'
    return response


@app.get('/')
def home(request):
    return app.render_template(
        os.path.join(TEMPLATES_DIR, 'home.html'),
        csrf_token=request.csrf_token,
        items=['Routing', 'Templates', 'JSON', 'Sessions', 'Uploads'],
        show_note=True,
        note='This line is <em>safe</em> HTML.',
    )


@app.post('/submit')
def submit(request):
    name = request.post('name', '').strip()
    return RedirectResponse(app.url_for('profile', name=name))


@app.get('/profile/<name>')
def profile(request, name):
    return app.render_template(
        os.path.join(TEMPLATES_DIR, 'profile.html'),
        name=name,
    )


@app.get('/api/ping')
def ping(request):
    return JSONResponse({'ok': True, 'message': 'pong'})


@app.get('/upload')
def upload_form(request):
    return app.render_template(
        os.path.join(TEMPLATES_DIR, 'upload.html'),
        csrf_token=request.csrf_token,
    )


@app.post('/upload')
def upload(request):
    info = {
        'has_file': 'file' in request.files,
        'filename': request.files.get('file', {}).get('filename', ''),
        'content_type': request.files.get('file', {}).get('content_type', ''),
        'notes': request.post('notes', ''),
    }
    request.session['last_upload'] = info['filename']
    return app.render_template(
        os.path.join(TEMPLATES_DIR, 'upload_result.html'),
        **info,
        last_upload=request.session.get('last_upload', ''),
    )


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
