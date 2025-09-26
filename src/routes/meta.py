from flask import redirect, url_for

from ..app import app

__all__ = ("robots_txt",)


@app.get("/robots.txt")
def robots_txt():
    response = redirect(url_for("static", filename="robots.txt"))
    response.headers["Content-Type"] = "text/plain"
    return response
