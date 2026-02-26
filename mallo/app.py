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
import html
from email.utils import formatdate
from wsgiref.simple_server import make_server, WSGIRequestHandler
from mallo.router import Router
from mallo.request import Request
from mallo.response import Response
from mallo.template import render_template, render_template_file, set_default_template_folder
from mallo.config import MalloConfig
from mallo.utils import generate_etag
from mallo.hot_reload import HotReloader


class RouteGroup:
    """
    Route prefix group with optional default route options.
    """

    def __init__(self, app, prefix, middleware=None, route_defaults=None):
        self.app = app
        self.prefix = prefix.rstrip('/') or '/'
        self.middleware = middleware or []
        self.route_defaults = route_defaults or {}

    def _join(self, path):
        if not path.startswith('/'):
            path = '/' + path
        if self.prefix == '/':
            return path
        return self.prefix + path

    def route(self, path, methods=None, **options):
        merged = dict(self.route_defaults)
        merged.update(options)
        route_middleware = []
        route_middleware.extend(self.middleware)
        route_middleware.extend(merged.get('middleware') or [])
        merged['middleware'] = route_middleware
        return self.app.route(self._join(path), methods=methods, **merged)

    def get(self, path, **options):
        return self.route(path, methods=['GET'], **options)

    def post(self, path, **options):
        return self.route(path, methods=['POST'], **options)

    def put(self, path, **options):
        return self.route(path, methods=['PUT'], **options)

    def delete(self, path, **options):
        return self.route(path, methods=['DELETE'], **options)


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
        merged_config = dict(config)
        merged_config['static_url_path'] = merged_config.get('static_url_path', static_url_path)
        self.config_obj = MalloConfig(**merged_config)
        self.config = self.config_obj.as_dict()
        self.static_url_path = self.config_obj.get('static_url_path')
        set_default_template_folder(self.config_obj.get('template_folder'))
        self.router = Router()
        self.hot_reloader = None
        self.debug = self.config_obj.get('debug')
        self.live_reload = self.config_obj.get('live_reload')
        self._reload_token = f"{os.getpid()}-{time.time_ns()}"
        self.secret_key = self.config_obj.get('secret_key')
        self.csrf_protect = self.config_obj.get('csrf_protect')
        self._session_cookie = self.config_obj.get('session_cookie')
        self._session_store = {}
        self.before_request_funcs = []
        self.after_request_funcs = []
        self.middlewares = []
        self._db_bindings = []
        self.error_handlers = {}
        self._enable_logging = self.config_obj.get('enable_logging')
        self._security_headers = self.config_obj.get('security_headers')
        self._static_cache_seconds = self.config_obj.get('static_cache_seconds')
        self.logger = logging.getLogger('mallo')
        self._default_404 = os.path.join(os.path.dirname(__file__), 'defaults', '404.html')
        self._default_500 = os.path.join(os.path.dirname(__file__), 'defaults', '500.html')

        # Add static route if static folder exists
        self._setup_static_routing()


    def _setup_static_routing(self):
        """ Setup static file serving if static folder exists """
        static_folder = self.config_obj.get('static_folder')
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

    def route(self, path, methods=None, name=None, middleware=None, csrf=None):
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
            route_name = name or getattr(handler, '__name__', None)
            options = {
                'name': route_name,
                'middleware': middleware or [],
                'csrf': csrf
            }
            self.router.add_route(path, handler, methods, options=options)
            return handler
        return decorator

    def get(self, path, **options):
        """
        Shorthand for the route with GET method
        :param path:
        :return:
        """
        return self.route(path, methods=['GET'], **options)

    def post(self, path, **options):
        """
        Shorthand for route with POST method
        :param path:
        :return:
        """
        return self.route(path, methods=['POST'], **options)

    def put(self, path, **options):
        """
        Shorthand for route with PUT method
        :param path:
        :return:
        """
        return self.route(path, methods=['PUT'], **options)

    def delete(self, path, **options):
        """
        Shorthand for route with DELETE method
        :param path:
        :return:
        """
        return self.route(path, methods=['DELETE'], **options)

    def group(self, prefix, middleware=None, **route_defaults):
        """
        Create a route group with a shared URL prefix and default options.
        """
        return RouteGroup(self, prefix, middleware=middleware, route_defaults=route_defaults)

    def render_template(self, template_name, **context):
        """
        Render a template from any file path

        Args:
            template_name: template file name relative to template folder
            **context: Variable to pass to template

        Returns:
           Rendered template as a string

        Example:
          @app.route('/')
          def home(request):
              return app.render_template('home.html', name='Mallo User')


        :param template_name:
        :param context:
        :return:
        """
        auto_escape = self.config_obj.get('auto_escape')
        template_folder = self.config_obj.get('template_folder')
        return render_template(
            template_name,
            template_folder=template_folder,
            auto_reload=self.debug,
            auto_escape=auto_escape,
            **context
        )

    def before_request(self, func):
        self.before_request_funcs.append(func)
        return func

    def after_request(self, func):
        self.after_request_funcs.append(func)
        return func

    def init_db(self, database, request_attr='db'):
        """
        Bind a Database object to each request.
        Example:
            db = Database("sqlite:///app.db")
            app.init_db(db)
            # then inside handlers: request.db.fetchall(...)
        """
        self._db_bindings.append((request_attr, database))

        @self.before_request
        def _inject_db(request):
            setattr(request, request_attr, database)

    def middleware(self, func):
        """
        Register a middleware function.
        Signature: middleware(request, call_next) -> Response|str|dict|list
        """
        self.middlewares.append(func)
        return func

    def use(self, middleware_func):
        """
        Register middleware without decorator syntax.
        """
        self.middlewares.append(middleware_func)
        return middleware_func

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
            def clear(self):
                self._parent._session_dirty = True
                return super().clear()
            def pop(self, key, default=None):
                self._parent._session_dirty = True
                return super().pop(key, default)
            def update(self, *args, **kwargs):
                self._parent._session_dirty = True
                return super().update(*args, **kwargs)
            def setdefault(self, key, default=None):
                self._parent._session_dirty = True
                return super().setdefault(key, default)

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

    def _csrf_check(self, request, csrf_required=True):
        if not csrf_required:
            return True
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

        custom_path = self.config_obj.get(f'error_page_{status_code}')
        template_path = custom_path or default_path
        content = render_template_file(template_path, auto_reload=self.debug, auto_escape=True)
        return Response(content, status=status_code)

    def _user_routes_count(self):
        """
        Count application routes excluding static and internal reload endpoints.
        """
        static_prefix = f'{self.static_url_path}/'
        count = 0
        for route in self.router.routes:
            original = route.get('original_path', '')
            if original.startswith(static_prefix):
                continue
            if original == '/__mallo_reload__':
                continue
            count += 1
        return count

    def _print_startup_diagnostics(self):
        """
        Show concise startup diagnostics for common routing mistakes.
        """
        if self._user_routes_count() > 0:
            return
        print(" ! Warning: No application routes registered.")
        print("   Common causes:")
        print("   - Missing '@' before app.route/app.get/app.post")
        print("   - Route module not imported before app.run()")
        print("   - Route decorator used but function not executed")

    def _friendly_debug_error_response(self, exc):
        """
        Render a clear and non-overwhelming debug error page.
        """
        import traceback

        exc_type = html.escape(type(exc).__name__)
        exc_msg = html.escape(str(exc) or "No message")
        tb = html.escape(traceback.format_exc())

        body = f"""
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Mallo Debug Error</title>
    <style>
      body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f6f3ee; color: #1f1a15; }}
      .wrap {{ max-width: 780px; margin: 30px auto; padding: 0 16px; }}
      .card {{ background: #fffdf9; border: 1px solid #e8dece; border-radius: 14px; padding: 18px; }}
      .tag {{ display: inline-block; background: #f8e8de; color: #b6521a; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; }}
      h1 {{ margin: 10px 0 8px; font-size: 26px; }}
      p {{ margin: 0 0 12px; color: #5f5549; }}
      code {{ background: #f4efe7; padding: 2px 6px; border-radius: 6px; }}
      details {{ margin-top: 12px; }}
      pre {{ white-space: pre-wrap; word-break: break-word; background: #1a1f29; color: #eaf0ff; border-radius: 10px; padding: 12px; overflow: auto; }}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <span class="tag">Debug Error</span>
        <h1>{exc_type}</h1>
        <p>{exc_msg}</p>
        <p>Tip: fix the issue and refresh the page.</p>
        <details>
          <summary>Show traceback details</summary>
          <pre>{tb}</pre>
        </details>
      </div>
    </div>
  </body>
</html>
"""
        return Response(body, status=500)

    def _ensure_response(self, result):
        if isinstance(result, Response):
            return result

        
        # (body, status) or (body, status, headers)
        if isinstance(result, tuple):
            if len(result) == 2:
                body, status = result
                return Response(body, status=status)
            if len(result) == 3:
                body, status, headers = result
                return Response(body, status=status, headers=headers)
            raise ValueError("Invalid response tuple. Use (body, status) or (body, status, headers).")

        # Plain body value.
        return Response(result)

    def _process_outgoing(self, request, response, start_time):
        """
        Apply common response processing once.
        """
        if getattr(response, "_mallo_processed", False):
            return response

        response = self._apply_security_headers(response)
        self._ensure_session_cookie(request, response)
        if self._enable_logging:
            elapsed = (time.perf_counter() - start_time) * 1000
            self.logger.info('%s %s -> %s (%.2fms)', request.method, request.path, response.status, elapsed)
        response._mallo_processed = True
        return response

    def _run_middleware_chain(self, request, endpoint, middleware_list):
        """
        Run middleware chain and return the final result.
        """
        index = 0

        def call_next(req):
            nonlocal index
            if index >= len(middleware_list):
                return self._ensure_response(endpoint(req))
            current = middleware_list[index]
            index += 1
            return self._ensure_response(current(req, call_next))

        return call_next(request)

    def _dispatch_request(self, request, start_time, route_match=None):
        """
        Resolve route and produce a response.
        """
        if route_match is None:
            route_match = self.router.match(request.path, request.method, return_route=True)
        if route_match:
            handler, kwargs, route = route_match
            route_options = route.get('options', {})
            route_middleware = route_options.get('middleware') or []

            def endpoint(req):
                return handler(req, **kwargs)
            try:
                result = self._run_middleware_chain(request, endpoint, route_middleware)
                result = self._ensure_response(result)

                if self.debug:
                    self._set_no_cache_headers(result)
                if self.debug and self.live_reload:
                    result = self._attach_live_reload(result)

                for func in self.after_request_funcs:
                    result = func(request, result) or result

                return self._process_outgoing(request, result, start_time)
            except Exception as e:
                if self.debug:
                    error_response = self._friendly_debug_error_response(e)
                    if self.debug:
                        self._set_no_cache_headers(error_response)
                    return self._process_outgoing(request, error_response, start_time)
                error_response = self._handle_error(request, 500, self._default_500)
                return self._process_outgoing(request, error_response, start_time)

        response = self._handle_error(request, 404, self._default_404)
        if self.debug:
            self._set_no_cache_headers(response)
        return self._process_outgoing(request, response, start_time)


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
            response = self._process_outgoing(request, response, start_time)
            return response.to_wsgi(start_response)

        for func in self.before_request_funcs:
            result = func(request)
            if isinstance(result, Response):
                if self.debug:
                    self._set_no_cache_headers(result)
                result = self._process_outgoing(request, result, start_time)
                return result.to_wsgi(start_response)

        # Match route before CSRF so route-level options can be applied.
        route_match = self.router.match(request.path, request.method, return_route=True)
        route_options = route_match[2].get('options', {}) if route_match else {}
        route_csrf = route_options.get('csrf')
        csrf_required = self.csrf_protect if route_csrf is None else bool(route_csrf)

        # CSRF protection for unsafe methods
        if not self._csrf_check(request, csrf_required=csrf_required):
            response = Response('<h1>403 Forbidden</h1>', status=403)
            if self.debug:
                self._set_no_cache_headers(response)
            response = self._process_outgoing(request, response, start_time)
            return response.to_wsgi(start_response)

        try:
            result = self._run_middleware_chain(
                request,
                lambda req: self._dispatch_request(req, start_time, route_match=route_match),
                self.middlewares
            )
            response = self._ensure_response(result)
            response = self._process_outgoing(request, response, start_time)
            return response.to_wsgi(start_response)
        except Exception as e:
            if self.debug:
                error_response = self._friendly_debug_error_response(e)
                if self.debug:
                    self._set_no_cache_headers(error_response)
                error_response = self._process_outgoing(request, error_response, start_time)
                return error_response.to_wsgi(start_response)
            error_response = self._handle_error(request, 500, self._default_500)
            error_response = self._process_outgoing(request, error_response, start_time)
            return error_response.to_wsgi(start_response)

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
            if debug:
                self._print_startup_diagnostics()

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
