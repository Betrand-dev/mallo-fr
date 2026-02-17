"""
Response object for mallo Framework
"""

import json
from typing import Any, Dict, Optional

class Response:
    """
    Represents an HTTP response

    Example:
        return Response('hello world', status=200, header={'Content-Type': 'text/plain'})
    """
    def __init__(self, body='',status=200,headers=None,content_type='text/html'):
        self.body = body
        self.status = status
        self.headers = headers or {}

        # Set a content type if not already set
        if 'Content-Type' not in self.headers:
            if isinstance(body, (dict, list)):
                self.headers['Content-Type'] = 'application/json'
            else:
                self.headers['Content-Type'] =content_type

        #add default headers
        self.headers['Server'] = 'Mallo'

    def to_wsgi(self, start_response):
        """
        Convert to WSGI response

        :param start_response:
        :return:
        """
        status_map = {
            200: '200 ok',
            201: '201 Created',
            204: '204 No Content',
            301: '301 Moved Permanently',
            302: '302 Found',
            304: '304 Not Modified',
            400: '400 Bad Request',
            401: '401 Unauthorised',
            403: '403 Forbidden',
            404: '404 Not Found',
            405: '405 Method Not Allowed',
            418: "418 I'm a teapot",
            500: '500 Internal Server Error',
            502: '502 Bad Gateway',
            503: '503 Service Unavailable',
        }
        status_text = status_map.get(self.status, f'{self.status} Unknown')

        # Convert header to List of tuples
        headers_list = [(k,v) for k, v in self.headers.items()]

        start_response(status_text, headers_list)

        #Encode body if it is a string
        if isinstance(self.body, str):
            return [self.body.encode()]
        elif isinstance(self.body, (dict, list)):
            # Auto-convert dict/list to json
            return [json.dumps(self.body).encode()]
        else:
            return [self.body]

    def set_cookie(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False):
        """
        Set a cookie in the response

        :param key:
        :param value:
        :param max_age:
        :param expires:
        :param path:
        :param domain:
        :param secure:
        :param httponly:
        :return:
        """
        cookie = f'{key} = {value}'
        if max_age is not None:
            cookie += f'; Max-Age={max_age}'
        if expires is not None:
            cookie += f'; Expires={expires}'
        if path is not None:
            cookie += f'; Path={path}'
        if domain is not None:
            cookie += f'; Domain={domain}'
        if secure:
            cookie += '; Secure'
        if httponly:
            cookie += '; HttpOnly'

        self.headers['Set-Cookie'] = cookie

    def delete_cookie(self, key, path='/', domain=None):
        """
        Delete a cookie by setting it to expire immediately

        :param key:
        :param path:
        :param domain:
        :return:
        """
        self.set_cookie(key, '',expires='Thu, 01 Jan 1970 00:00:00 GMT', path=path, domain=domain)



class JSONResponse(Response):
    """
    Response with JSON content

    """
    def __init__(self, data, status=200, headers=None):
        super().__init__(
            body=json.dumps(data),
            status=status,
            headers=headers,
            content_type='application/json'
        )


class RedirectResponse(Response):
    """
    Redirect response
    """
    def __init__(self, location, status=302):
        super().__init__(
            body='',
            status=status,
            headers={'Location': location}
        )

class FileResponse(Response):
    """
    File download response
    """
    def __init__(self, filepath, filename=None, status=200, headers=None):
        with open(filepath, 'rb') as f:
            content = f.read()

        if filename is None:
            import os
            filename = os.path.basename(filepath)

        headers = headers or {}
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        super().__init__(
            body=content,
            status=status,
            headers=headers,
            content_type='application/octet-stream'
        )
