"""
Mallo - A lightweight Web framework with Hot reload
"""

from mallo.app import Mallo
from mallo.request import Request
from mallo.response import Response
from mallo.cli import cli
from mallo.template import render_template, render_template_file

__version__ = "0.3.0a6"
__all__ = ['Mallo', 'Request', 'Response', 'cli', 'render_template', 'render_template_file' ]
