"""
Command line interface for Mallo framework.
"""

import argparse
import os
import re
import subprocess
import sys
import platform
from pathlib import Path
from textwrap import dedent


def _is_valid_project_name(name: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9._-]+$", name or ""))


def _write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"File already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_project(name: str, template_folder: str = "templates", static_folder: str = "static", force: bool = False) -> int:
    """Create a new Mallo project scaffold safely."""
    if not name or not name.strip():
        print("Error: project name cannot be empty.")
        return 1
    if not _is_valid_project_name(name):
        print("Error: project name may only contain letters, numbers, '.', '_' or '-'.")
        return 1
    if not template_folder.strip() or not static_folder.strip():
        print("Error: template/static folder names cannot be empty.")
        return 1

    project_dir = Path(name).resolve()
    if project_dir.exists() and not project_dir.is_dir():
        print(f"Error: path exists and is not a directory: {project_dir}")
        return 1
    if project_dir.exists() and not force and any(project_dir.iterdir()):
        print(f"Error: directory is not empty: {project_dir}")
        print("Use --force to overwrite scaffold files.")
        return 1

    print(f"Creating new Mallo project: {name}")
    project_dir.mkdir(parents=True, exist_ok=True)

    app_content = dedent(
        f"""\
        \"\"\"
        Mallo application
        \"\"\"

        from mallo import Mallo

        app = Mallo(__name__, template_folder='{template_folder}', static_folder='{static_folder}')

        @app.get('/')
        def home(request):
            return app.render_template('index.html')

        @app.get('/hello/<name>')
        def hello(request, name):
            return f'<h1>Hello, {{name}}!</h1>'

        @app.get('/api/data')
        def api_data(request):
            return {{'message': 'Hello from Mallo!', 'status': 'success'}}

        if __name__ == '__main__':
            app.run(debug=True, use_reloader=True)
        """
    )

    index_content = dedent(
        """\
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Mallo Framework</title>
          <link rel="stylesheet" href="/static/style.css" />
        </head>
        <body>
          <div class="page">
            <div class="top">
              <div class="brand">Mallo Framework</div>
              <div class="chip">Minimal customizable Web Core &bull; Fast Iteration</div>
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

            <div class="footer">Mallo - lightweight Python web framework</div>
          </div>
        </body>
        </html>
        """
    )

    css_content = dedent(
        """\
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

        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');

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
        """
    )

    readme_content = dedent(
        f"""\
        # {name}

        Generated by Mallo CLI.

        ## Run

        ```bash
        python app.py
        ```
        """
    )

    gitignore_content = dedent(
        """\
        __pycache__/
        *.pyc
        .venv/
        """
    )

    try:
        _write_file(project_dir / "app.py", app_content, force)
        _write_file(project_dir / template_folder / "index.html", index_content, force)
        _write_file(project_dir / static_folder / "style.css", css_content, force)
        _write_file(project_dir / "README.md", readme_content, force)
        _write_file(project_dir / ".gitignore", gitignore_content, force)
    except Exception as exc:
        print(f"Error: failed to create project files: {exc}")
        return 1

    print(f"Project '{name}' created successfully.")
    print(f"cd {name}")
    print("python app.py")
    return 0


def run_server(app_path: str, host: str, port: int, debug: bool, reload: bool) -> int:
    """Run a Mallo application via gunicorn."""
    if platform.system().lower().startswith("win"):
        print("Gunicorn is not supported on Windows. Use 'python app.py' or run on Linux/WSL.")
        return 1

    env = os.environ.copy()
    env["MALLO_DEBUG"] = "1" if debug else "0"
    env["MALLO_LIVE_RELOAD"] = "1" if debug else "0"

    cmd = [
        "gunicorn",
        app_path,
        "--bind",
        f"{host}:{port}",
    ]
    if reload:
        cmd.append("--reload")

    try:
        result = subprocess.run(cmd, env=env, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: gunicorn is not installed. Install it with: pip install gunicorn")
        return 1


def cli() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Mallo web framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--template-folder", default="templates", help="Template folder name")
    create_parser.add_argument("--static-folder", default="static", help="Static folder name")
    create_parser.add_argument("--force", action="store_true", help="Overwrite scaffold files if they exist")

    run_parser = subparsers.add_parser("run", help="Run the application")
    run_parser.add_argument("app", nargs="?", default="app:app", help="WSGI app path, e.g. app:app")
    run_parser.add_argument("--host", default="localhost", help="Host to bind to")
    run_parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    run_parser.add_argument("--debug", action="store_true", default=True, help="Enable debug mode")
    run_parser.add_argument("--no-debug", action="store_true", help="Disable debug mode")
    run_parser.add_argument("--no-reload", action="store_true", help="Disable hot reload")

    args = parser.parse_args()

    if args.command == "create":
        code = create_project(
            args.name,
            template_folder=args.template_folder,
            static_folder=args.static_folder,
            force=args.force,
        )
        sys.exit(code)
    if args.command == "run":
        debug = args.debug and not args.no_debug
        reload = not args.no_reload and debug
        code = run_server(args.app, args.host, args.port, debug, reload)
        sys.exit(code)

    parser.print_help()


if __name__ == "__main__":
    cli()
