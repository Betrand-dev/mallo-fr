"""
Simple template rendering engine for Mallo framework
"""
import os
import re
import html
from typing import Dict, Any

class TemplateEngine:
    """
    Simple template engine with variable substitution and basic control structures
    """

    def __init__(self):
        self.cache = {}

    def render(self, template_path: str, auto_reload: bool = False, auto_escape: bool = True, **context) -> str:
        """
        Render a template file with context variables
        Supports:
               {{ variable }} -variable substitution
               {% if conditions %}....{% endif %} - if statements
               {% for item in list %}...{% endfor %} - For loops

        :param template_path:
        :param context:
        :return:
        """
        if not os.path.exists(template_path):
            return _template_error_page(
                "Template not found",
                "Mallo could not find the template file.",
                template_path
            )

        current_mtime = os.path.getmtime(template_path)
        cached = self.cache.get(template_path)

        if cached and (not auto_reload or cached['mtime'] == current_mtime):
            template = cached['template']
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            self.cache[template_path] = {
                'template': template,
                'mtime': current_mtime
            }

        # Render the template
        try:
            return self._render_string(template, context, auto_escape=auto_escape)
        except Exception as exc:
            return _template_error_page(
                "Template render error",
                "Mallo failed while rendering this template.",
                f"{template_path}\n{type(exc).__name__}: {exc}"
            )

    def _render_string(self, template: str, context: Dict[str, Any], auto_escape: bool = True) -> str:
        """
        Render a template with context

        :param template:
        :param context:
        :return:
        """
        def resolve_var(var_name: str, ctx: Dict[str, Any]):
            parts = var_name.split('.')
            value = ctx
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, '')
                else:
                    value = getattr(value, part, '')
            return value

        def render_value(expr: str, ctx: Dict[str, Any]) -> str:
            parts = [part.strip() for part in expr.split('|')]
            var_name = parts[0]
            filters = parts[1:]

            value = resolve_var(var_name, ctx)
            text = str(value)

            if 'safe' in filters:
                return text
            if auto_escape:
                return html.escape(text)
            return text

        token_re = re.compile(r'{%\s*(if|for|endif|endfor)\b([^%]*)%}')
        pos = 0
        tokens = []

        for match in token_re.finditer(template):
            if match.start() > pos:
                tokens.append(('text', template[pos:match.start()]))
            keyword = match.group(1)
            expr = match.group(2).strip()
            tokens.append((keyword, expr))
            pos = match.end()

        if pos < len(template):
            tokens.append(('text', template[pos:]))

        def parse_tokens(token_list, index=0):
            nodes = []
            while index < len(token_list):
                kind, value = token_list[index]
                if kind == 'text':
                    nodes.append(('text', value))
                    index += 1
                elif kind == 'if':
                    index += 1
                    inner, index = parse_tokens(token_list, index)
                    nodes.append(('if', value, inner))
                elif kind == 'for':
                    index += 1
                    inner, index = parse_tokens(token_list, index)
                    nodes.append(('for', value, inner))
                elif kind in ('endif', 'endfor'):
                    index += 1
                    return nodes, index
                else:
                    index += 1
            return nodes, index

        def eval_condition(expr: str, ctx: Dict[str, Any]) -> bool:
            expr = expr.strip()
            negate = False
            if expr.startswith('not '):
                negate = True
                expr = expr[4:].strip()
            value = resolve_var(expr, ctx)
            return (not value) if negate else bool(value)

        def render_nodes(nodes, ctx: Dict[str, Any]) -> str:
            output = []
            for node in nodes:
                kind = node[0]
                if kind == 'text':
                    output.append(re.sub(r'{{(.*?)}}', lambda m: render_value(m.group(1).strip(), ctx), node[1]))
                elif kind == 'if':
                    expr, inner = node[1], node[2]
                    if eval_condition(expr, ctx):
                        output.append(render_nodes(inner, ctx))
                elif kind == 'for':
                    expr, inner = node[1], node[2]
                    if ' in ' not in expr:
                        continue
                    var_name, list_name = [part.strip() for part in expr.split(' in ', 1)]
                    items = resolve_var(list_name, ctx)
                    if items is None:
                        continue
                    for item in items:
                        new_ctx = dict(ctx)
                        new_ctx[var_name] = item
                        output.append(render_nodes(inner, new_ctx))
            return ''.join(output)

        nodes, _ = parse_tokens(tokens)
        return render_nodes(nodes, context)

# Global template engine instance
_engine = TemplateEngine()
_default_template_folder = 'templates'


def set_default_template_folder(folder: str) -> None:
    """
    Set the global default template folder used by render_template().
    """
    global _default_template_folder
    _default_template_folder = folder or 'templates'

def _template_error_page(title: str, message: str, detail: str = "") -> str:
    safe_title = html.escape(title)
    safe_message = html.escape(message)
    safe_detail = html.escape(detail)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mallo Template Error</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #f6f3ee; color: #1f1a15; }}
    .wrap {{ max-width: 760px; margin: 28px auto; padding: 0 16px; }}
    .card {{ background: #fffdf9; border: 1px solid #e8dece; border-radius: 14px; padding: 18px; }}
    .tag {{ display: inline-block; border-radius: 999px; padding: 4px 10px; background: #f8e8de; color: #b6521a; font-size: 12px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; }}
    h1 {{ margin: 10px 0 8px; font-size: 26px; }}
    p {{ margin: 0 0 10px; color: #5f5549; }}
    pre {{ margin: 0; background: #1a1f29; color: #eaf0ff; border-radius: 10px; padding: 12px; white-space: pre-wrap; word-break: break-word; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <span class="tag">Template Error</span>
      <h1>{safe_title}</h1>
      <p>{safe_message}</p>
      <pre>{safe_detail}</pre>
    </div>
  </div>
</body>
</html>
"""

def render_template(
    template_name: str,
    template_folder: str | None = None,
    auto_reload: bool = False,
    auto_escape: bool = True,
    **context
) -> str:
    """
    Render a template from the configured template folder.

    Args:
        template_name: Template name relative to template_folder (e.g. "index.html")
        template_folder: Folder that contains templates (default: "templates")
        auto_reload: Reload template file when changed
        auto_escape: Escape variables by default
        **context: Context variables for rendering
    """
    folder = template_folder or _default_template_folder
    if not os.path.isdir(folder):
        return _template_error_page(
            "Template folder not found",
            "Mallo expected a template folder but it does not exist.",
            folder
        )

    template_path = os.path.join(folder, template_name)
    return render_template_file(
        template_path,
        auto_reload=auto_reload,
        auto_escape=auto_escape,
        **context
    )

def render_template_file(template_path: str, auto_reload: bool = False, auto_escape: bool = True, **context)->str:
    """
    Render a template from file path with context

    :param template_path:
    :param context:
    :return:
    """
    return _engine.render(template_path, auto_reload=auto_reload, auto_escape=auto_escape, **context)
