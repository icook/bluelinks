import wtforms as field
import wtforms.validators as validators
from flask.ext.wtf import Form
from flask.ext.security.forms import unique_user_email, RegisterFormMixin
from . import models as m


password_length = validators.Length(min=6, max=128, message='PASSWORD_INVALID_LENGTH')


def unique_user_name(form, field):
    if m.User.query.filter_by(username=field.data).first() is not None:
        msg = "Email address already in use!"
        raise validators.ValidationError(msg)


class ExtendedRegisterForm(Form):
    username = field.TextField(
        'Username',
        validators=[unique_user_name])
    email = field.TextField(
        'Email',
        validators=[validators.Required(), validators.Email(), unique_user_email])
    password = field.PasswordField(
        'Password',
        validators=[validators.Required(), password_length,
                    validators.EqualTo('confirm', message='Passwords must match')])
    confirm = field.PasswordField('Repeat Password')
    submit = field.SubmitField("Register")

    to_dict = RegisterFormMixin.to_dict
