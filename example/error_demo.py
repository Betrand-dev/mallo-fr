from mallo import Mallo


app = Mallo(__name__, live_reload=True)


@app.get("/")
def home(request):
    return """
    <h1>Mallo Error Demo</h1>
    <p>Open <a href="/boom">/boom</a> to trigger an intentional error.</p>
    """


@app.get("/boom")
def boom(request):
    # Intentional error so you can preview the debug error UI.
    data = {"name": "mallo"}
    return data["name"]


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
