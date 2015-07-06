import os
import sqlalchemy

from flask import (render_template, Blueprint, send_from_directory, request,
                   url_for, redirect, current_app, jsonify)
from flask.ext.login import login_required, logout_user, login_user, current_user

from . import root, db, lm
from .forms import SubmissionForm
from .models import User, Subreddit, Post, Comment


api_bp = Blueprint('api', __name__)


@api_bp.route("/vote/<subreddit>/<id>/<direction>")
@login_required
def vote(id, direction, subreddit):
    post = Post(id=id, subreddit_name=subreddit)
    post.vote(direction)
    return jsonify(success=True)


@api_bp.route("/post_comment/<parent>", methods=["POST"])
@api_bp.route("/post_comment/", methods=["POST"])
@login_required
def comment(parent=None):
    parent = Comment.query.filter_by(id=parent).first()
    path = "{}/{}".format(parent.path, parent.id) if parent else ""
    comment = Comment(
        path=path,
        user=current_user._get_current_object(),
        text=request.values['contents'],
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify(success=True)
