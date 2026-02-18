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

from mallo import Mallo, render_template

app = Mallo(__name__)

@app.route('/')
def home(request):
    return render_template('index.html')

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
    index_content = '''
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mallo Framework</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');

    :root {
      --bg: #f8f5ef;
      --paper: #fffdf9;
      --ink: #16130f;
      --muted: #655a4d;
      --accent: #bb5a1d;
      --accent-2: #1f7a7a;
      --line: #e7dccd;
      --shadow: 0 24px 60px rgba(31, 22, 12, 0.14);
      --radius: 18px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: "Outfit", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1000px 500px at 10% 0%, #efe4d3 0%, rgba(239, 228, 211, 0) 60%),
        radial-gradient(900px 450px at 90% 0%, #ddeeea 0%, rgba(221, 238, 234, 0) 56%),
        var(--bg);
      line-height: 1.5;
    }

    .page {
      max-width: 1080px;
      margin: 0 auto;
      padding: 38px 20px 70px;
    }

    .top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
    }

    .brand {
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-size: 0.86rem;
      color: var(--accent);
    }

    .chip {
      border: 1px solid var(--line);
      background: var(--paper);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 0.84rem;
      color: var(--muted);
    }

    .hero {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 34px;
      margin-bottom: 20px;
      position: relative;
      overflow: hidden;
    }

    .hero::after {
      content: "";
      position: absolute;
      right: -60px;
      top: -60px;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(187, 90, 29, 0.2) 0%, rgba(187, 90, 29, 0) 70%);
      pointer-events: none;
    }

    h1 {
      margin: 0 0 12px;
      font-size: clamp(2rem, 5vw, 3.5rem);
      line-height: 1.05;
      max-width: 760px;
    }

    .lead {
      margin: 0;
      max-width: 700px;
      color: var(--muted);
      font-size: 1.05rem;
    }

    .actions {
      display: flex;
      gap: 10px;
      margin-top: 22px;
      flex-wrap: wrap;
    }

    .btn {
      text-decoration: none;
      border-radius: 12px;
      padding: 11px 16px;
      font-weight: 600;
      transition: transform 140ms ease, box-shadow 140ms ease;
      display: inline-block;
    }

    .btn.primary {
      background: var(--accent);
      color: #fff;
      box-shadow: 0 12px 24px rgba(187, 90, 29, 0.28);
    }

    .btn.secondary {
      background: #fff;
      color: var(--ink);
      border: 1px solid var(--line);
    }

    .btn:hover {
      transform: translateY(-1px);
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 14px;
      margin-top: 14px;
    }

    .card {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 20px;
    }

    .card h3 {
      margin: 0 0 8px;
      font-size: 1.05rem;
    }

    .card p {
      margin: 0;
      color: var(--muted);
      font-size: 0.96rem;
    }

    .span-4 { grid-column: span 4; }
    .span-6 { grid-column: span 6; }
    .span-8 { grid-column: span 8; }

    .snippet {
      background: #151a22;
      color: #ecf1ff;
      border-radius: 14px;
      padding: 18px;
      margin-top: 14px;
      border: 1px solid #202838;
      font-family: "Space Mono", monospace;
      font-size: 0.9rem;
      overflow-x: auto;
    }

    .snippet .prompt {
      color: #8dd6d0;
    }

    .footer {
      margin-top: 20px;
      color: var(--muted);
      font-size: 0.9rem;
      text-align: center;
    }

    @media (max-width: 900px) {
      .span-4,
      .span-6,
      .span-8 {
        grid-column: span 12;
      }
      .hero {
        padding: 26px;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="top">
      <div class="brand">Mallo Framework</div>
      <div class="chip">Minimal Web Core • Fast Iteration</div>
    </div>

    <section class="hero">
      <h1>Build web apps with a clean Python workflow, and help shape Mallo.</h1>
      <p class="lead">
        Mallo gives you routing, templates, static files, error pages, and development reload in a small readable codebase.
        You keep control while moving quickly, and your contributions directly improve the framework.
      </p>
      <div class="actions">
        <a class="btn primary" href="https://pypi.org/project/mallo/" target="_blank" rel="noreferrer">Install from PyPI</a>
        <a class="btn secondary" href="https://github.com/Betrand-dev/mallo-fr.git" target="_blank" rel="noreferrer">Contribute on GitHub</a>
      </div>
    </section>

    <section class="grid">
      <article class="card span-4">
        <h3>Simple Routing</h3>
        <p>Register endpoints with decorators and typed URL params without extra ceremony.</p>
      </article>
      <article class="card span-4">
        <h3>Template Rendering</h3>
        <p>Use <code>render_template()</code> for the <code>templates/</code> folder or <code>render_template_file()</code> for explicit paths.</p>
      </article>
      <article class="card span-4">
        <h3>Safe Defaults</h3>
        <p>Auto-escaped templates, security headers, CSRF checks, and structured error pages.</p>
      </article>
      <article class="card span-6">
        <h3>Production Path</h3>
        <p>Run with Gunicorn, package from PyPI, and keep improving with versioned pre-releases.</p>
      </article>
      <article class="card span-6">
        <h3>Developer Experience</h3>
        <p>Live reload in debug mode, readable internals, and a small surface area for faster onboarding.</p>
      </article>
    </section>

    <div class="snippet">
<span class="prompt">from</span> mallo <span class="prompt">import</span> Mallo, render_template<br><br>
app = Mallo(__name__)<br><br>
@app.get('/')<br>
def home(request):<br>
&nbsp;&nbsp;&nbsp;&nbsp;return render_template('index.html', title='Welcome to Mallo')<br><br>
if __name__ == '__main__':<br>
&nbsp;&nbsp;&nbsp;&nbsp;app.run(debug=True)
    </div>

    <section class="grid">
      <article class="card span-8">
        <h3>Call for Contributors</h3>
        <p>
          Mallo is actively evolving. If you work with Python web apps, your help can directly improve architecture,
          developer experience, and production readiness.
        </p>
      </article>
      <article class="card span-4">
        <h3>Start Here</h3>
        <p>Open issues, propose improvements, or submit a pull request for docs, tests, or core features.</p>
      </article>
      <article class="card span-4">
        <h3>Good First PRs</h3>
        <p>Template improvements, middleware polish, test coverage, and CLI usability.</p>
      </article>
      <article class="card span-4">
        <h3>Join the Core Work</h3>
        <p>Help harden sessions, request parsing, and deployment workflows for stable production use.</p>
      </article>
      <article class="card span-4">
        <h3>Repository</h3>
        <p><a href="https://github.com/Betrand-dev/mallo-fr.git" target="_blank" rel="noreferrer">github.com/Betrand-dev/mallo-fr</a></p>
      </article>
    </section>

    <div class="footer">Mallo • lightweight Python web framework</div>
  </div>
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
