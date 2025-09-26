from flask_wtf import FlaskForm
from wtforms.fields import EmailField, PasswordField, SubmitField


class LoginForm(FlaskForm):
    email = EmailField(id="login-email")
    password = PasswordField(id="login-password")

    submit = SubmitField(id="login-submit")
