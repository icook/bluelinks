import wtforms as field
import wtforms.validators as validators
from flask import request
from flask.ext.wtf import Form
from flask.ext.security.forms import unique_user_email, RegisterFormMixin, NextFormMixin
from flask.ext.security.utils import get_message, verify_and_update_password
from flask.ext.security.confirmable import requires_confirmation
from . import models as m
from .application import security


password_length = validators.Length(min=6, max=128, message='PASSWORD_INVALID_LENGTH')


class EitherOr(object):
    """ Allows entry of one or the other """
    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError:
            raise validators.ValidationError(field.gettext("Invalid field name '%s'.") % self.fieldname)
        if field.data and other.data:
            d = {
                'other_label': hasattr(other, 'label') and other.label.text or self.fieldname,
                'other_name': self.fieldname,
                'this_label': hasattr(field, 'label') and field.label.text or field.name,
                'this_name': field.name
            }
            message = self.message
            if message is None:
                message = field.gettext('You may only enter either %(other_label)s or %(this_label)s.')

            raise validators.ValidationError(message % d)


def unique_user_name(form, field):
    if m.User.query.filter_by(username=field.data).first() is not None:
        msg = "Email address already in use!"
        raise validators.ValidationError(msg)


class LoginForm(Form, NextFormMixin):
    username = field.TextField('Username', validators=[validators.Required()])
    password = field.PasswordField('Password', validators=[validators.Required()])
    remember = field.BooleanField('Remember Me')
    submit = field.SubmitField("Login")

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = request.args.get('next', '')

    def validate(self):
        if not super(LoginForm, self).validate():
            return False

        self.user = m.User.query.filter_by(username=self.username.data).first()

        if self.user is None:
            self.user.errors.append(get_message('USER_DOES_NOT_EXIST')[0])
            return False
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD_NOT_SET')[0])
            return False
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message('INVALID_PASSWORD')[0])
            return False
        if requires_confirmation(self.user):
            self.user.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active():
            self.user.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True


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


class LinkSubmissionForm(Form):
    title = field.TextField(
        'Title',
        validators=[validators.Length(min=10, max=256)])
    url = field.TextField(
        'URL',
        validators=[validators.URL()])
    nsfw = field.BooleanField('NSFW')
    submit = field.SubmitField("Submit")


class TextSubmissionForm(Form):
    title = field.TextField(
        'Title',
        validators=[validators.Length(min=10, max=256)])
    contents = field.TextAreaField(
        'Contents',
        validators=[validators.Length(min=10)])
    nsfw = field.BooleanField('NSFW')
    submit = field.SubmitField("Submit")


class CreateCommunityForm(Form):
    name = field.TextField('Name', validators=[
        validators.Length(min=4, max=32),
        validators.Regexp("^[a-zA-Z0-9-_]+$")
    ])
    submit = field.SubmitField("Create")
