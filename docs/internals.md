**Internals**

**Request Flow**
1. WSGI server calls `Mallo.__call__(environ, start_response)`
1. `Request(environ)` parses method, path, headers, body, form, JSON, cookies
1. Session is loaded if `secret_key` is set and CSRF token is ensured
1. CSRF is validated for unsafe methods
1. `Router.match(path, method)` finds a handler and kwargs
1. The handler runs and returns a string, dict, or `Response`
1. If not already `Response`, it is wrapped in `Response`
1. If `debug=True`, cache headers are disabled
1. If live reload is enabled and HTML response, a script is injected
1. Response is converted to WSGI and returned

**Router Compilation**
1. Route patterns are converted to regex with named params
1. Param types are cast to `int` or `float`, or left as string
1. Match returns handler and kwargs

**Static File Serving**
1. If a `static` folder exists at startup, a route is registered
1. Matching `/static/<path:filename>` serves the file
1. Unknown files return 404
1. ETag and Last-Modified headers are set
1. `If-None-Match` with matching ETag returns 304

**Template Rendering**
1. `render_template_file()` loads template content
1. The template is cached unless `auto_reload=True`
1. `{{ variable }}` substitutions are performed

**Live Reload**
1. The reloader spawns a subprocess and restarts it when file signatures change
1. The browser polling endpoint is `/__mallo_reload__`
1. HTML responses get a reload script injected when `debug=True` and `live_reload=True`
