from flask_wtf import FlaskForm
from wtforms.fields import EmailField, PasswordField, StringField, SubmitField


class RegisterForm(FlaskForm):
    full_name = StringField(id="register-name", name="register-name")
    email = EmailField(id="register-email", name="register-email")
    password = PasswordField(id="register-password", name="register-password")

    submit = SubmitField(id="register-submit", name="register-submit")
