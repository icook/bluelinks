import os
import sqlalchemy

from flask import (render_template, Blueprint, send_from_directory, request,
                   g, url_for, redirect, current_app)
from flask.ext.login import login_required, logout_user, login_user, current_user

from . import root, db, lm
from .forms import SubmissionForm
from .models import User, Subreddit, Post


main = Blueprint('main', __name__)


@main.before_request
def add_globals():
    g.subreddits = Subreddit.query.all()


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route("/r/<name>/comments/<post_id>")
def post(name, post_id):
    post = Post.query.filter_by(id=post_id).one()
    nested = []
    last_obj = None
    for comment in post.comments:
        # It's a subcomment...
        if last_obj is None:
            nested.append(comment)
            comment.parent = last_obj
            comment.depth = 0
        else:
            # Bubble back up until we find the parent of this comment
            while not comment.path.startswith(last_obj.path):
                last_obj = comment.parent
            last_obj.children.append(comment)
            comment.depth = last_obj.depth + 1
            comment.parent = last_obj
        last_obj = comment
        last_obj.children = []
    return render_template('post.html', post=post, comments=nested)


@main.route("/u/<username>")
def profile(username):
    obj = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=obj)


@main.route("/submit/<name>", methods=["POST", "GET"])
@login_required
def subreddit_submission(name):
    sub = Subreddit.query.filter_by(name=name).one()
    form = SubmissionForm()
    if form.validate_on_submit():
        post = Post(
            subreddit=sub,
            user=current_user._get_current_object(),
            url=form.url.data or None,
            text=form.contents.data or None,
            title=form.title.data,
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.post', name=name, post_id=post.id))
    return render_template('submission.html', form=form)


@main.route("/r/<name>")
def subreddit(name):
    sub = Subreddit.query.filter_by(name=name).first()
    return render_template('subreddit.html', subreddit=sub)


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
