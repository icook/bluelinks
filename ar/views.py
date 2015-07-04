import os
import sqlalchemy

from flask import (render_template, Blueprint, send_from_directory, request,
                   url_for, redirect, current_app)
from flask.ext.login import login_required, logout_user, login_user

from . import root, db, lm
from .models import User, Subreddit


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


@main.route("/r/<subreddit>")
@login_required
def subreddit(name):
    sub = Subreddit.query.filter_by(name=name).first()
    return render_template('subreddit.html', subreddit=sub)


@main.route("/account")
@login_required
def account():
    return render_template('account.html')


@main.route("/")
def home():
    subreddits = Subreddit.query
    return render_template('home.html', subreddits=subreddits)


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
