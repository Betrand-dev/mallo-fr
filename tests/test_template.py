from mallo.template import TemplateEngine


def test_template_if_and_for():
    engine = TemplateEngine()
    template = "Hello {% if show %}Yes{% endif %} {% for item in items %}{{ item }} {% endfor %}"
    result = engine._render_string(template, {'show': True, 'items': ['A', 'B']})
    assert "Hello Yes" in result
    assert "A" in result
    assert "B" in result
