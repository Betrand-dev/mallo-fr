"""
Core Application for Mallo framework
"""

import os
import sys
import time
import hmac
import hashlib
import secrets
import logging
from email.utils import formatdate
from wsgiref.simple_server import make_server, WSGIRequestHandler
from mallo.router import Router
from mallo.request import Request
from mallo.response import Response
from mallo.template import render_template_file
from mallo.utils import generate_etag
from mallo.hot_reload import HotReloader

class Mallo:
    """
    Main application class for Mallo framework
    Example:
        app = Mallo(__name__)
        @app.route("/")
        def home(request):
            return "<h1>Hello, Mallo!</h1>"

    """

    def __init__(self, import_name, static_url_path="/static", **config):
        self.import_name = import_name
        self.static_url_path = static_url_path
        self.config = config
        self.router = Router()
        self.hot_reloader = None
        env_debug = os.environ.get('MALLO_DEBUG')
        self.debug = config.get('debug', env_debug == '1')
        env_live = os.environ.get('MALLO_LIVE_RELOAD')
        self.live_reload = config.get('live_reload', env_live == '1' if env_live is not None else True)
        self._reload_token = f"{os.getpid()}-{time.time_ns()}"
        self.secret_key = config.get('secret_key')
        self.csrf_protect = config.get('csrf_protect', True)
        self._session_cookie = config.get('session_cookie', 'mallo_session')
        self._session_store = {}
        self.before_request_funcs = []
        self.after_request_funcs = []
        self.error_handlers = {}
        self._enable_logging = config.get('enable_logging', True)
        self._security_headers = config.get('security_headers', True)
        self._static_cache_seconds = config.get('static_cache_seconds')
        if self._static_cache_seconds is None:
            self._static_cache_seconds = 0 if self.debug else 3600
        self.logger = logging.getLogger('mallo')
        self._default_404 = os.path.join(os.path.dirname(__file__), 'defaults', '404.html')
        self._default_500 = os.path.join(os.path.dirname(__file__), 'defaults', '500.html')

        # Add static route if static folder exists
        self._setup_static_routing()


    def _setup_static_routing(self):
        """ Setup static file serving if static folder exists """
        static_folder = self.config.get('static_folder', 'static')
        if os.path.exists(static_folder):
            @self.route(f'{self.static_url_path}/<path:filename>')
            def serve_static(request, filename):
                filepath = os.path.join(static_folder, filename)
                if os.path.exists(filepath) and os.path.isfile(filepath):
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    etag = generate_etag(content)
                    last_modified = formatdate(os.path.getmtime(filepath), usegmt=True)
                    if request.headers.get('If-None-Match') == etag:
                        response = Response('', status=304)
                        response.headers['ETag'] = etag
                        response.headers['Last-Modified'] = last_modified
                        return response
                    response = Response(content, headers={
                        'Content-Type': self._guess_mime_type(filename)
                    })
                    response.headers['ETag'] = etag
                    response.headers['Last-Modified'] = last_modified
                    if self._static_cache_seconds > 0:
                        response.headers['Cache-Control'] = f'public, max-age={self._static_cache_seconds}'
                    else:
                        response.headers['Cache-Control'] = 'no-store'
                    return response
                return Response('File not found', status = 404)

    def route(self, path, methods=None):
        """
        Decorator to register a route

        Args:
            path: URL path (e.g., '/', '/user/<name>')
            methods: List of HTTP methods (default: ['GET'])

        Example:
            @app.route('/hello/<name>')
            def hello(request, name):
                return f'Hello, {name}!'

        :param path
        :param methods
        :return:
        """
        if methods is None:
            methods = ['GET']

        def decorator(handler):
            self.router.add_route(path, handler, methods)
            return handler
        return decorator

    def get(self, path):
        """
        Shorthand for the route with GET method
        :param path:
        :return:
        """
        return self.route(path, methods=['GET'])

    def post(self, path):
        """
        Shorthand for route with POST method
        :param path:
        :return:
        """
        return self.route(path, methods=['POST'])

    def put(self, path):
        """
        Shorthand for route with PUT method
        :param path:
        :return:
        """
        return self.route(path, methods=['PUT'])

    def delete(self, path):
        """
        Shorthand for route with DELETE method
        :param path:
        :return:
        """
        return self.route(path, methods=['DELETE'])

    def render_template(self, template_path, **context):
        """
        Render a template from any file path

        Args:
            template_path: path to template file (absolute or relative)
            **context: Variable to pass to template

        Returns:
           Rendered template as a string

        Example:
          @app.route('/')
          def home(request):
              return app.render_template('templates/home.html', name = 'Mallo User')


        :param template_path:
        :param context:
        :return:
        """
        auto_escape = self.config.get('auto_escape', True)
        return render_template_file(template_path, auto_reload=self.debug, auto_escape=auto_escape, **context)

    def before_request(self, func):
        self.before_request_funcs.append(func)
        return func

    def after_request(self, func):
        self.after_request_funcs.append(func)
        return func

    def errorhandler(self, status_code: int):
        def decorator(handler):
            self.error_handlers[status_code] = handler
            return handler
        return decorator

    def url_for(self, handler_name: str, **kwargs):
        return self.router.url_for(handler_name, **kwargs)

    def _sign_session_id(self, session_id: str) -> str:
        secret = (self.secret_key or '').encode()
        return hmac.new(secret, session_id.encode(), hashlib.sha256).hexdigest()

    def _make_session_cookie(self, session_id: str) -> str:
        return f"{session_id}|{self._sign_session_id(session_id)}"

    def _load_session(self, request):
        if not self.secret_key:
            request.session = None
            request.session_id = None
            request._session_dirty = False
            return

        raw = request.cookies.get(self._session_cookie, '')
        session_id = None
        if raw and '|' in raw:
            sid, sig = raw.split('|', 1)
            if hmac.compare_digest(sig, self._sign_session_id(sid)):
                session_id = sid

        if not session_id:
            session_id = secrets.token_urlsafe(24)

        if session_id not in self._session_store:
            self._session_store[session_id] = {}

        class SessionData(dict):
            def __init__(self, parent, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._parent = parent
            def __setitem__(self, key, value):
                self._parent._session_dirty = True
                return super().__setitem__(key, value)
            def __delitem__(self, key):
                self._parent._session_dirty = True
                return super().__delitem__(key)

        request.session_id = session_id
        request.session = SessionData(request)
        request.session.update(self._session_store[session_id])
        request._session_dirty = False

        if 'csrf_token' not in request.session:
            request.session['csrf_token'] = secrets.token_urlsafe(32)
        request.csrf_token = request.session.get('csrf_token')

    def _ensure_session_cookie(self, request, response):
        if not self.secret_key or request.session_id is None:
            return
        if request._session_dirty:
            self._session_store[request.session_id] = dict(request.session)
            cookie_value = self._make_session_cookie(request.session_id)
            response.set_cookie(self._session_cookie, cookie_value, path='/')

    def _csrf_check(self, request):
        if not self.secret_key or not self.csrf_protect:
            return True
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        token = None
        if request.headers.get('X-Csrf-Token'):
            token = request.headers.get('X-Csrf-Token')
        elif request.form:
            token = request.form.get('csrf_token')
        elif request.json:
            token = request.json.get('csrf_token')

        return token and token == request.csrf_token

    def _apply_security_headers(self, response):
        if not self._security_headers:
            return response
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'same-origin')
        return response

    def _handle_error(self, request, status_code, default_path):
        handler = self.error_handlers.get(status_code)
        if handler:
            result = handler(request)
            if not isinstance(result, Response):
                result = Response(result, status=status_code)
            return result

        custom_path = self.config.get(f'error_page_{status_code}')
        template_path = custom_path or default_path
        content = render_template_file(template_path, auto_reload=self.debug, auto_escape=True)
        return Response(content, status=status_code)


    def __call__(self, environ, start_response):
        """
        WSGI application entry point
        :param environ:
        :param start_response:
        :return:
        """
        start_time = time.perf_counter()
        request = Request(environ)
        self._load_session(request)

        # Lightweight endpoint used by browser-side live reload polling.
        if request.path == '/__mallo_reload__':
            response = Response(
                self._reload_token,
                headers={
                    'Content-Type': 'text/plain',
                    'Cache-Control': 'no-store, no-cache, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
            response = self._apply_security_headers(response)
            self._ensure_session_cookie(request, response)
            return response.to_wsgi(start_response)

        for func in self.before_request_funcs:
            result = func(request)
            if isinstance(result, Response):
                if self.debug:
                    self._set_no_cache_headers(result)
                result = self._apply_security_headers(result)
                self._ensure_session_cookie(request, result)
                return result.to_wsgi(start_response)

        # CSRF protection for unsafe methods
        if not self._csrf_check(request):
            response = Response('<h1>403 Forbidden</h1>', status=403)
            if self.debug:
                self._set_no_cache_headers(response)
            response = self._apply_security_headers(response)
            self._ensure_session_cookie(request, response)
            return response.to_wsgi(start_response)

        #find matching route
        route_match = self.router.match(request.path, request.method)

        if route_match:
            handler, kwargs = route_match
            try:
                # Call handler with request and capture kwargs
                result = handler(request, **kwargs)

                # Convert result to Response if needed
                if not isinstance(result, Response):
                    result = Response(result)

                if self.debug:
                    self._set_no_cache_headers(result)
                if self.debug and self.live_reload:
                    result = self._attach_live_reload(result)

                result = self._apply_security_headers(result)
                for func in self.after_request_funcs:
                    result = func(request, result) or result
                self._ensure_session_cookie(request, result)
                if self._enable_logging:
                    elapsed = (time.perf_counter() - start_time) * 1000
                    self.logger.info('%s %s -> %s (%.2fms)', request.method, request.path, result.status, elapsed)
                return result.to_wsgi(start_response)
            except Exception as e:
                if self.debug:
                    import traceback
                    error_response = Response(
                        f"<h1>Error</h1><pre>{traceback.format_exc()}</pre>",
                        status=500
                    )
                    self._ensure_session_cookie(request, error_response)
                    error_response = self._apply_security_headers(error_response)
                    return error_response.to_wsgi(start_response)
                error_response = self._handle_error(request, 500, self._default_500)
                self._ensure_session_cookie(request, error_response)
                error_response = self._apply_security_headers(error_response)
                return error_response.to_wsgi(start_response)
        else:
            # 404 Not Found
            response = self._handle_error(request, 404, self._default_404)
            if self.debug:
                self._set_no_cache_headers(response)
            response = self._apply_security_headers(response)
            self._ensure_session_cookie(request, response)
            if self._enable_logging:
                elapsed = (time.perf_counter() - start_time) * 1000
                self.logger.info('%s %s -> %s (%.2fms)', request.method, request.path, response.status, elapsed)
            return response.to_wsgi(start_response)

    def _set_no_cache_headers(self, response):
        """
        Prevent browser caching while debugging.
        """
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    def _attach_live_reload(self, response):
        """
        Inject browser auto-refresh script into HTML responses in debug mode.
        """
        content_type = response.headers.get('Content-Type', '')
        if not isinstance(response.body, str):
            return response
        if 'text/html' not in content_type.lower():
            return response
        if '__mallo_reload__' in response.body:
            return response

        script = """
<script>
(function () {
  var token = null;
  function checkReload() {
    fetch('/__mallo_reload__?t=' + Date.now(), { cache: 'no-store' })
      .then(function (res) { return res.text(); })
      .then(function (value) {
        value = value.trim();
        if (token === null) {
          token = value;
          return;
        }
        if (token !== value) {
          window.location.reload();
        }
      })
      .catch(function () {});
  }
  setInterval(checkReload, 1000);
  checkReload();
})();
</script>
"""

        body = response.body
        if '</body>' in body:
            body = body.replace('</body>', script + '\n</body>', 1)
        else:
            body = body + script
        response.body = body
        return response


    def run(self, host='localhost', port=8000, debug=False, use_reloader=True):
        """
        Run the development server

        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
            use_reloader: Enable hot reload

        :param host:
        :param port:
        :param debug:
        :param use_reloader:
        :return:
        """
        self.debug = debug

        in_reloader_subprocess = os.environ.get('MALLO_HOT_RELOAD') == '1'
        if use_reloader and debug and not in_reloader_subprocess:
            # Start with hot reload
            self.hot_reloader = HotReloader(self)
            self.hot_reloader.run(host, port)
        else:
            # Start Normally
            print(f" * Running on http://{host}:{port}/")
            print(f" * Debug Mode: {'on' if debug else 'off'}")

            class QuietReloadRequestHandler(WSGIRequestHandler):
                def log_message(self, format, *args):
                    try:
                        request_line = args[0] if args else ""
                        if "__mallo_reload__" in str(request_line):
                            return
                    except Exception:
                        pass
                    super().log_message(format, *args)

            server = make_server(host, port, self, handler_class=QuietReloadRequestHandler)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n * Server stopped")

    def _guess_mime_type(self, filename):
        """
        Guess MIME type from filename extension
        :param filename:
        :return:
        """
        ext_map ={
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.txt': 'text/plain'
        }

        ext = os.path.splitext(filename)[1].lower()
        return ext_map.get(ext, 'application/octet-stream')
