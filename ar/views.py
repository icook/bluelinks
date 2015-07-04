import os
import sqlalchemy

from flask import (render_template, Blueprint, send_from_directory, request,
                   url_for, redirect, current_app)
from flask.ext.login import login_required, logout_user, login_user

from . import root, db, lm
from .models import User


main = Blueprint('main', __name__)


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route("/u/<username>")
@login_required
def profile(username):
    obj = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=obj)


@main.route("/account")
@login_required
def account():
    return render_template('account.html')


@main.route("/")
def home():
    return render_template('home.html')


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@lm.user_loader
def load_user(userid):
    try:
        return User.query.filter_by(id=userid).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return None
