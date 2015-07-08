import os
import sqlalchemy

from flask import (render_template, Blueprint, send_from_directory, request,
                   g, url_for, redirect, current_app)
from flask.ext.login import login_required, logout_user, login_user, current_user

from . import root, db, lm, redis_store
from .forms import TextSubmissionForm, LinkSubmissionForm, CreateCommunityForm
from .models import User, Community, Post, Comment


main = Blueprint('main', __name__)


@main.before_request
def add_globals():
    g.communities = Community.query.all()
    g.site_title = current_app.config.get('site_title', 'Skeleton Project')


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route("/c/<name>/comments/<post_id>")
def post(name, post_id):
    post = Post.query.filter_by(id=post_id).one()

    scores = {int(a): b for a, b in
              redis_store.zrange("pc{}".format(post.id), 0, -1, withscores=True)}
    nested = []
    last_obj = None

    def sort_comments(obj):
        return obj.score_val
    for comment in post.comments:
        # Bubble back up until we find the parent of this comment
        while last_obj is not None and not comment.path.startswith(last_obj.path):
            last_obj = last_obj.parent

        if last_obj is None:
            nested.append(comment)
            comment.parent = last_obj
            comment.depth = 0
        else:
            last_obj.children.append(comment)
            comment.depth = last_obj.depth + 1
            comment.parent = last_obj
        last_obj = comment
        last_obj.children = []
        last_obj.score_val = scores.get(comment.id, 0)

    sub = Community.query.filter_by(name=name).first()
    return render_template('post.html', post=post, comments=nested, community=sub, sort_comments=sort_comments)


@main.route("/c/<name>/comments/<post_id>/<comment_id>")
def permalink(name, post_id, comment_id):
    post = Post.query.filter_by(id=post_id).one()
    subcomments = Comment.query.filter_by(id=comment_id).one().subcomments

    scores = {int(a): b for a, b in
              redis_store.zrange("pc{}".format(post.id), 0, -1, withscores=True)}
    nested = []
    last_obj = None

    def sort_comments(obj):
        return obj.score_val
    for comment in subcomments:

        if last_obj is None:
            nested.append(comment)
            comment.parent = last_obj
            comment.depth = 0
        else:
            last_obj.children.append(comment)
            comment.depth = last_obj.depth + 1
            comment.parent = last_obj
        last_obj = comment
        last_obj.children = []
        last_obj.score_val = scores.get(comment.id, 0)

    sub = Community.query.filter_by(name=name).first()
    return render_template('post.html', post=post, comments=nested, community=sub, sort_comments=sort_comments)


@main.route("/u/<username>")
def profile(username):
    obj = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=obj)


@main.route("/create_sub", methods=["POST", "GET"])
@login_required
def create_community():
    form = CreateCommunityForm()
    if form.validate_on_submit():
        sub = Community(
            name=form.name.data,
            user=current_user._get_current_object(),
        )
        db.session.add(sub)
        db.session.commit()
        return redirect(url_for('main.community', name=sub.name))
    return render_template('submission.html', form=form)


@main.route("/submit/<name>/link", methods=["POST", "GET"])
@login_required
def community_link_submission(name):
    sub = Community.query.filter_by(name=name).one()
    form = LinkSubmissionForm()
    if form.validate_on_submit():
        post = Post(
            community=sub,
            user=current_user._get_current_object(),
            url=form.url.data,
            text=None,
            title=form.title.data,
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.post', name=name, post_id=post.id))
    return render_template('submission.html', form=form)


@main.route("/submit/<name>/text", methods=["POST", "GET"])
@login_required
def community_text_submission(name):
    sub = Community.query.filter_by(name=name).one()
    form = TextSubmissionForm()
    if form.validate_on_submit():
        post = Post(
            community=sub,
            user=current_user._get_current_object(),
            url=None,
            text=form.contents.data,
            title=form.title.data,
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.post', name=name, post_id=post.id))
    return render_template('submission.html', form=form)


@main.route("/c/<name>")
def community(name):
    sub = Community.query.filter_by(name=name).first()
    return render_template('community.html', community=sub)


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
