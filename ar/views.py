import os
import datetime
import sqlalchemy

from flask import (render_template, Blueprint, send_from_directory, request,
                   g, url_for, redirect, current_app, abort)
from flask.ext.login import login_required, logout_user, login_user, current_user

from .application import root, db, lm, redis_store
from .forms import TextSubmissionForm, LinkSubmissionForm, CreateCommunityForm
from .models import User, Community, Post, Comment
from .hot import hot


main = Blueprint('main', __name__)


@main.before_request
def add_globals():
    g.communities = Community.query.all()


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(root, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route("/c/<name>/comments/<post_id>")
def post(name, post_id):
    sort = request.args.get('sort', 'hot')
    post = Post.query.filter_by(id=post_id).one()
    redis_key = "pc{}" if sort == 'top' else "pch{}"

    scores = {int(a): b for a, b in
              redis_store.zrange(redis_key.format(post.id), 0, -1, withscores=True)}
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

    comm = Community.query.filter_by(name=name).first()
    return render_template('post.html', post=post, comments=nested,
                           community=comm, sort_comments=sort_comments)


@main.route("/c/<name>/comments/<post_id>/<comment_id>/")
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

    comm = Community.query.filter_by(name=name).first()
    return render_template('post.html', post=post, comments=nested,
                           community=comm, sort_comments=sort_comments)


@main.route("/u/<username>/")
def profile(username):
    obj = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=obj)


@main.route("/create_community", methods=["POST", "GET"])
@login_required
def create_community():
    form = CreateCommunityForm()
    if form.validate_on_submit():
        comm = Community(
            name=form.name.data,
            user=current_user._get_current_object(),
        )
        db.session.add(comm)
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.warn(e, exc_info=True)
            db.session.rollback()
            abort(500)

        return redirect(url_for('main.community', name=comm.name))
    return render_template('submission.html', form=form)


@main.route("/submit/<name>/link", methods=["POST", "GET"])
@login_required
def community_link_submission(name):
    comm = Community.query.filter_by(name=name).one()
    form = LinkSubmissionForm()
    if form.validate_on_submit():
        post = Post(
            community=comm,
            user=current_user._get_current_object(),
            url=form.url.data,
            text=None,
            title=form.title.data,
        )
        db.session.add(post)
        db.session.flush()
        redis_store.vote_cmd(keys=(), args=("p", post.id, current_user.id, 1, comm.name))
        db.session.commit()
        return redirect(url_for('main.post', name=name, post_id=post.id))
    return render_template('submission.html', form=form)


@main.route("/submit/<name>/text", methods=["POST", "GET"])
@login_required
def community_text_submission(name):
    comm = Community.query.filter_by(name=name).one()
    form = TextSubmissionForm()
    if form.validate_on_submit():
        post = Post(
            community=comm,
            user=current_user._get_current_object(),
            url=None,
            text=form.contents.data,
            title=form.title.data,
        )
        db.session.add(post)
        db.session.flush()
        redis_store.vote_cmd(keys=(), args=("p", post.id, current_user.id, 1, comm.name))
        db.session.commit()
        return redirect(url_for('main.post', name=name, post_id=post.id))
    return render_template('submission.html', form=form)


@main.route("/c/<name>/", methods=["POST", "GET"])
def community(name):
    sort = request.args.get('sort', 'hot')
    redis_key = "h{}" if sort == 'hot' else "{}"
    page = int(request.args.get('page', 0))
    offset = page * 50
    post_ids = redis_store.zrange(redis_key.format(name), offset, offset + 50)
    post_ids.reverse()
    post_ids = [int(pid) for pid in post_ids]
    posts = {p.id: p for p in Post.query.filter(Post.id.in_(post_ids))}
    posts = [posts[pid] for pid in post_ids]
    comm = Community.query.filter_by(name=name).first()
    if request.method == "POST":
        if comm in current_user.subscriptions:
            current_user.subscriptions.remove(comm)
        else:
            current_user.subscriptions.append(comm)
        db.session.commit()
    return render_template('community.html', community=comm, posts=posts, page=page)


@main.route("/account")
@login_required
def account():
    return render_template('account.html')


def generate_frontpage():
    if current_user.is_authenticated():
        subs = [sub.name for sub in current_user.subscriptions]
    else:
        subs = ["pics", "funny", "videos", "news", "science", "meta"]
    sort = request.args.get('sort', 'hot')
    redis_key = "h{}" if sort == 'hot' else "{}"
    posts = {}
    for sub in subs:
        data = redis_store.zrange(redis_key.format(sub), 0, 100, withscores=True)
        for post_id, score in data:
            posts[int(post_id)] = score
    return sorted(posts, key=posts.get, reverse=True)


@main.route("/")
def home():
    post_ids = generate_frontpage()
    page = int(request.args.get('page', 0))
    offset = page * 50
    posts = {p.id: p for p in Post.query.filter(Post.id.in_(post_ids[offset:50]))}
    posts = [posts[pid] for pid in post_ids]
    return render_template('home.html', posts=posts, page=page)


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
