"""
Routing System for Mallo framework
"""
import re
from typing import Dict, List, Tuple, Optional, Callable

class Router:
    """
    Handles URL routing with support for dynamic  parameters

    Dynamic route example:
      /user/<name>           -> matches /user/betrand, passes {'name': 'betrand'}
      /post/<int:id>         -> matches /post/123, passes {'id': 123}
      /file/<path:filepath>  -> matches /file/documents/test.txt

    """

    def __init__(self):
        self.routes = [] # List of (patterns, handler, methods)

    def add_route(self, path: str, handler: Callable, methods: List[str]):
        """
        Add a new route to the router

        Args:
            path: URL path with optional parameters
            handler: Function to handle the route
            methods: List of HTTP methods

        :param path:
        :param handler:
        :param methods:
        """
        # Convert path to regex pattern
        pattern = self._path_to_pattern(path)

        for method in methods:
            self.routes.append({
                'pattern': pattern,
                'handler': handler,
                'method': method.upper(),
                'original_path': path
            })

    def _path_to_pattern(self, path: str):
        """
        Convert a path with parameter to a regex pattern

        Supports:
                <name>     -> string parameter
                <int: id>  -> integer parameter
                <float: value> -> float parameter
                <path: filepath> -> path parameter

        Example:
              /user/<int:id>/<name> -> /user/123/betrand
        :param path:
        :return:
        """
        param_names = []

        # Replace parameter placeholders
        def replace_param(match):
            param = match.group(1)

            # Check for type specification
            if ':' in param:
                param_type, param_name = param.split(':')
                param_names.append((param_name, param_type))

                # Return appropriate regex pattern
                if param_type == 'int':
                    return r'(\d+)'
                elif param_type == 'float':
                    return r'(\d+\.?\d*)'
                elif param_type == 'path':
                    return r'(.+)'
                else: # string (default)
                    return r'([^/]+)'
            else:
                # Default to string
                param_names.append((param, 'str'))
                return r'([^/]+)'

        #replace <....> with regex patterns
        pattern = re.sub(r'<([^>]+)>', replace_param, path)

        #compile the regex
        regex = re.compile(f'^{pattern}$')

        return  regex, param_names


    def match(self, path: str, method: str) -> Optional[Tuple[Callable,Dict]]:
        """
        Match a path and method to a route

        Returns:
              Tuple of (handler, kwargs) or None if no match

        :param path:
        :param method:
        :return:
        """
        for route in self.routes:
            if route['method'] != method.upper():
                continue

            pattern, param_types = route['pattern']
            match = pattern.match(path)

            if match:
                # Build kwargs from captured groups
                kwargs = {}
                for i, (name, param_type) in enumerate(param_types):
                    value = match.group(i + 1)

                    # Convert to appropriate type
                    if param_type == 'int':
                        value = int(value)
                    elif param_type == 'float':
                        value = float(value)
                    # 'str' and 'path' remain as string

                    kwargs[name] = value

                return route['handler'], kwargs

        return None

    def url_for(self, handler_name: str, **kwargs) -> str:
        """
        Generate URL for a named route (to be implemented)
        :param handler_name:
        :param kwargs:
        :return:
        """
        for route in self.routes:
            handler = route['handler']
            if getattr(handler, '__name__', None) != handler_name:
                continue

            path = route['original_path']

            def replace_param(match):
                param = match.group(1)
                if ':' in param:
                    _, param_name = param.split(':', 1)
                else:
                    param_name = param

                if param_name not in kwargs:
                    raise KeyError(f"Missing route param: {param_name}")
                return str(kwargs[param_name])

            return re.sub(r'<([^>]+)>', replace_param, path)

        raise KeyError(f"No route found for handler: {handler_name}")
