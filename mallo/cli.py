"""
Command line interface for Mallo framework
"""

import argparse
import os
import sys
import subprocess
import platform


def create_project(name):
    """Create a new Mallo project"""
    print(f"Creating new Mallo project: {name}")

    # Create project directory
    os.makedirs(name, exist_ok=True)

    # Create basic structure
    os.makedirs(os.path.join(name, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(name, 'static'), exist_ok=True)

    # Create app.py
    app_content = '''"""
Mallo application
"""

from mallo import Mallo

app = Mallo(__name__)

@app.route('/')
def home(request):
    return app.render_template('templates/index.html', name='Mallo User')

@app.route('/hello/<name>')
def hello(request, name):
    return f'<h1>Hello, {name}!</h1>'

@app.route('/api/data')
def api_data(request):
    return {'message': 'Hello from Mallo!', 'status': 'success'}

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
'''

    with open(os.path.join(name, 'app.py'), 'w') as f:
        f.write(app_content)

    # Create index.html
    index_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Mallo App</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Welcome to Mallo, {{ name }}!</h1>
    <p>Your lightweight Flask alternative is working!</p>
    <p>Try:</p>
    <ul>
        <li><a href="/hello/World">/hello/World</a></li>
        <li><a href="/api/data">/api/data</a></li>
    </ul>
</body>
</html>
'''

    with open(os.path.join(name, 'templates', 'index.html'), 'w') as f:
        f.write(index_content)

    print(f"Project '{name}' created successfully!")
    print(f"cd {name}")
    print("python app.py")


def run_server(app_path, host, port, debug, reload):
    """Run a Mallo application via gunicorn"""
    if platform.system().lower().startswith('win'):
        print("Gunicorn is not supported on Windows. Use 'python app.py' or run on Linux.")
        return

    env = os.environ.copy()
    env['MALLO_DEBUG'] = '1' if debug else '0'
    env['MALLO_LIVE_RELOAD'] = '1' if debug else '0'

    cmd = [
        'gunicorn',
        app_path,
        '--bind',
        f'{host}:{port}',
    ]
    if reload:
        cmd.append('--reload')

    subprocess.run(cmd, env=env, check=False)


def cli():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Mallo web framework CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create project command
    create_parser = subparsers.add_parser('create', help='Create a new project')
    create_parser.add_argument('name', help='Project name')

    # Run command (for future use)
    run_parser = subparsers.add_parser('run', help='Run the application')
    run_parser.add_argument('app', nargs='?', default='app:app', help='WSGI app path, e.g. app:app')
    run_parser.add_argument('--host', default='localhost', help='Host to bind to')
    run_parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    run_parser.add_argument('--debug', action='store_true', default=True, help='Enable debug mode')
    run_parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    run_parser.add_argument('--no-reload', action='store_true', help='Disable hot reload')

    args = parser.parse_args()

    if args.command == 'create':
        create_project(args.name)
    elif args.command == 'run':
        debug = args.debug and not args.no_debug
        reload = not args.no_reload and debug
        run_server(args.app, args.host, args.port, debug, reload)
    else:
        parser.print_help()


if __name__ == '__main__':
    cli()
