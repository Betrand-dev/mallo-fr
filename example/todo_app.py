import os
from mallo import Mallo
from mallo.response import RedirectResponse


BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Mallo(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    secret_key="todo-dev-secret",
    live_reload=True,
)


def _todo_state(request):
    todos = request.session.get("todos", [])
    next_id = request.session.get("next_todo_id", 1)
    return todos, next_id


@app.get("/")
def home(request):
    todos, _ = _todo_state(request)
    return app.render_template(
        "todo.html",
        todos=todos,
        csrf_token=request.csrf_token,
    )


@app.post("/add")
def add_todo(request):
    title = request.post("title", "").strip()
    if not title:
        return RedirectResponse("/")

    todos, next_id = _todo_state(request)
    todos.append(
        {
            "id": next_id,
            "title": title,
            "done": False,
        }
    )

    request.session["todos"] = todos
    request.session["next_todo_id"] = next_id + 1
    return RedirectResponse("/")


@app.post("/toggle/<int:id>")
def toggle_todo(request, id):
    todos, _ = _todo_state(request)
    for todo in todos:
        if todo["id"] == id:
            todo["done"] = not todo["done"]
            break
    request.session["todos"] = todos
    return RedirectResponse("/")


@app.post("/delete/<int:id>")
def delete_todo(request, id):
    todos, _ = _todo_state(request)
    todos = [todo for todo in todos if todo["id"] != id]
    request.session["todos"] = todos
    return RedirectResponse("/")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
