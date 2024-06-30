from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        Regexp(r'(?=.*[A-Z])', message="Must contain at least one uppercase letter"),
        Regexp(r'(?=.*[a-z])', message="Must contain at least one lowercase letter"),
        Regexp(r'(?=.*\d)', message="Must contain at least one digit"),
        Regexp(r'(?=.*[@$!%*?&])', message="Must contain at least one special character")
    ], render_kw={"id": "passwordField"})
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
