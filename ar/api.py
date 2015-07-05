import os
import sqlalchemy

from flask import (render_template, Blueprint, send_from_directory, request,
                   url_for, redirect, current_app, jsonify)
from flask.ext.login import login_required, logout_user, login_user, current_user

from . import root, db, lm
from .forms import SubmissionForm
from .models import User, Subreddit, Post


api_bp = Blueprint('api', __name__)


@api_bp.route("/vote/<id>/<direction>")
@login_required
def vote(id, direction):
    post = Post(id=id)
    post.vote(direction)
    return jsonify(success=True)
