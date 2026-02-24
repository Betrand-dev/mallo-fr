import os
from mallo import Mallo, Database
from mallo.response import RedirectResponse


BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "mallo_demo.db")

app = Mallo(__name__)
db = Database(f"sqlite:///{DB_PATH}")
app.init_db(db)

# Create a tiny table once.
db.execute(
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL
    )
    """
)


@app.get("/")
def home(request):
    rows = request.db.fetchall("SELECT id, title FROM notes ORDER BY id DESC")
    items = "".join(
        [f"<li>#{row['id']} - {row['title']}</li>" for row in rows]
    )
    return f"""
    <h1>Mallo DB Demo</h1>
    <form method="post" action="/add">
      <input name="title" placeholder="New note..." required />
      <button type="submit">Add</button>
    </form>
    <ul>{items}</ul>
    """


@app.post("/add")
def add(request):
    title = request.post("title", "").strip()
    if title:
        request.db.execute(
            "INSERT INTO notes (title) VALUES (:title)",
            {"title": title}
        )
    return RedirectResponse("/")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
