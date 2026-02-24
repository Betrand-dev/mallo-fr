"""
Configuration utilities for Mallo.
"""

import os


class MalloConfig:
    """
    App config with environment variable overrides.
    Explicit constructor values take precedence over environment values.
    """

    DEFAULTS = {
        'debug': False,
        'live_reload': True,
        'static_url_path': '/static',
        'static_folder': 'static',
        'template_folder': 'templates',
        'auto_escape': True,
        'enable_logging': True,
        'security_headers': True,
        'static_cache_seconds': None,
        'secret_key': None,
        'csrf_protect': True,
        'session_cookie': 'mallo_session',
        'error_page_404': None,
        'error_page_500': None,
    }

    ENV_MAP = {
        'debug': ('MALLO_DEBUG', 'bool'),
        'live_reload': ('MALLO_LIVE_RELOAD', 'bool'),
        'static_url_path': ('MALLO_STATIC_URL_PATH', 'str'),
        'static_folder': ('MALLO_STATIC_FOLDER', 'str'),
        'template_folder': ('MALLO_TEMPLATE_FOLDER', 'str'),
        'auto_escape': ('MALLO_AUTO_ESCAPE', 'bool'),
        'enable_logging': ('MALLO_ENABLE_LOGGING', 'bool'),
        'security_headers': ('MALLO_SECURITY_HEADERS', 'bool'),
        'static_cache_seconds': ('MALLO_STATIC_CACHE_SECONDS', 'int_or_none'),
        'secret_key': ('MALLO_SECRET_KEY', 'str'),
        'csrf_protect': ('MALLO_CSRF_PROTECT', 'bool'),
        'session_cookie': ('MALLO_SESSION_COOKIE', 'str'),
        'error_page_404': ('MALLO_ERROR_PAGE_404', 'str'),
        'error_page_500': ('MALLO_ERROR_PAGE_500', 'str'),
    }

    def __init__(self, **overrides):
        self._data = dict(self.DEFAULTS)

        for key, (env_key, cast_type) in self.ENV_MAP.items():
            raw = os.environ.get(env_key)
            if raw is None:
                continue
            self._data[key] = self._cast(raw, cast_type)

        for key, value in overrides.items():
            self._data[key] = value

        if self._data['static_cache_seconds'] is None:
            self._data['static_cache_seconds'] = 0 if self._data['debug'] else 3600

    def _cast(self, value, cast_type):
        if cast_type == 'str':
            return value
        if cast_type == 'bool':
            return str(value).strip().lower() in ('1', 'true', 'yes', 'on')
        if cast_type == 'int_or_none':
            text = str(value).strip().lower()
            if text in ('none', 'null', ''):
                return None
            return int(text)
        return value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def as_dict(self):
        return dict(self._data)
