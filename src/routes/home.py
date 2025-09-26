from flask import render_template
from flask_login import current_user, login_required

from ..app import app

__all__ = ("index", "chat")


@app.get("/")
@app.get("/home/")
@app.get("/index/")
def index():
    return render_template("index.jinja", user=current_user)


@app.get("/chat/")
@login_required
def chat():
    return render_template("chat.jinja", user=current_user)
