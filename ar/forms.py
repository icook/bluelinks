import wtforms as field
import wtforms.validators as validators
from flask.ext.wtf import Form
from flask.ext.security.forms import unique_user_email, RegisterFormMixin
from . import models as m


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


class SubmissionForm(Form):
    title = field.TextField(
        'Title',
        validators=[validators.Length(min=15, max=512)])
    url = field.TextField(
        'URL',
        validators=[EitherOr('contents'), validators.URL(), validators.Optional()])
    contents = field.TextAreaField(
        'Contents',
        validators=[validators.Length(min=256), validators.Optional()])
    nsfw = field.BooleanField('NSFW')
    submit = field.SubmitField("Submit")
