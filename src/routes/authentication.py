from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..app import Users, app, db
from ..forms import LoginForm, RegisterForm

__all__ = ("register", "login", "login_post", "register_post")


@app.get("/register/")
def register():
    login_form, register_form = LoginForm(), RegisterForm()

    return render_template("login-register.jinja", active_tab="register", login_form=login_form, register_form=register_form)


@app.get("/login/")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    login_form, register_form = LoginForm(), RegisterForm()
    return render_template("login-register.jinja", active_tab="login", login_form=login_form, register_form=register_form)


@app.post("/authentication-login/")
def login_post():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.execute(db.select(Users).filter_by(email=login_form.email.data)).scalar_one_or_none()
        if user and user.password == login_form.password.data:
            login_user(user, remember=True)
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("index"))
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
            return redirect(url_for("login"))

    return redirect(url_for("index"))


@app.post("/authentication-register/")
def register_post():
    register_form = RegisterForm()

    if (
        register_form.validate_on_submit()
        and register_form.email.data
        and register_form.password.data
        and register_form.full_name.data
    ):
        existing_user = db.session.execute(db.select(Users).filter_by(email=register_form.email.data)).scalar_one_or_none()
        if existing_user is None:
            new_user = Users(name=register_form.full_name.data, email=register_form.email.data, password=register_form.password.data)

            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("A user with that email already exists.", "danger")
            return redirect(url_for("register"))
    else:
        flash("Please fill out all fields.", "danger")
        return redirect(url_for("register"))


@app.get("/logout/")
@app.post("/logout/")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
