"""
Request object for Mallo framework
"""

import json
from urllib.parse import parse_qs
from typing import Dict, Any, Optional
from mallo.utils import parse_multipart_form

class Request:
    """
    Represents an HTTP request

    Attributes:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        headers: Dictionary of HTTP headers
        query: Dictionary of query parameter
        form: Dictionary of form data (fo post requests)
        json: parsed JSON body (if applicable)
        body: Raw request body
        cookies: Dictionary of cookies
    """

    def __init__(self, environ):
        self.eviron = environ
        self.method = environ['REQUEST_METHOD'].upper()
        self.path = environ['PATH_INFO']
        self.query_string = environ.get('QUERY_STRING', '')

        # Parse headers
        self.headers = self._parse_headers(environ)

        # Parse query parameter
        self.query = parse_qs(self.query_string)
        # Flatten single-value query params
        self.query = {k: v[0] if len(v) == 1 else v for k, v in self.query.items()}

        #parse body
        self.body = self._get_body()

        # Parse form data
        self.form = {}
        self.files = {}
        self.json = None

        content_type = self.headers.get('Content-Type', '')
        if self.method == 'POST' and self.body:
            if 'application/x-www-form-urlencoded' in content_type:
                self.form = parse_qs(self.body.decode())
                # Flatten single-value form fields
                self.form = {k: v[0] if len(v) == 1 else v for k, v in self.form.items()}
            elif 'application/json' in content_type:
                try:
                    self.json = json.loads(self.body.decode())
                except:
                    self.json = None
            elif 'multipart/form-data' in content_type:
                try:
                    form, files = parse_multipart_form(self.headers, self.body)
                    self.form = form
                    self.files = files
                except:
                    self.form = {}
                    self.files = {}

        # Parse cookies
        self.cookies = self._parse_cookies()

    def _parse_headers(self, environ):
        """
        Parse HTTP headers from WSGI environ

        :param environ:
        :return:
        """
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_','-').title()
                headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                headers[key.replace('_','-').title()] = value
        return headers

    def _get_body(self):
        """
        Read request body

        :return:
        """
        try:
            content_length = int(self.eviron.get('CONTENT_LENGTH', 0))
            if content_length > 0:
                return self.eviron['wsgi.input'].read(content_length)
        except:
            pass
        return b''

    def _parse_cookies(self):
        """
        Parse cookies from header

        :return:
        """
        cookies = {}
        cookie_header = self.headers.get('Cookie', '')

        if cookie_header:
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    cookies[name] = value

        return cookies

    def get(self, key, default=None):
        """
        Get a query parameter

        :param key:
        :param default:
        :return:
        """
        return self.query.get(key, default)

    def post(self, key, default=None):
        """
        Get a form parameter

        :param key:
        :param default:
        :return:
        """
        return self.form.get(key, default)

    def is_xhr(self):
        """
        Check if request is AJAX

        :return:
        """
        return self.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def __repr__(self):
        return f'<Request {self.method} {self.path}>'
