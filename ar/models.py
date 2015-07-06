import datetime

from sqlalchemy.orm import remote, foreign
from flask.ext.security import UserMixin, RoleMixin
from flask.ext.login import current_user
from flask import url_for
from .model_lib import base
from . import db, redis_store


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(base, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    # Authentication
    # ========================================================================
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class Subreddit(base):
    name = db.Column(db.String, primary_key=True)


class Post(base):
    id = db.Column(db.Integer, primary_key=True)
    # Either url or text, not both...
    url = db.Column(db.String)
    text = db.Column(db.Unicode)
    title = db.Column(db.Unicode, nullable=False)

    subreddit_name = db.Column(db.ForeignKey('subreddit.name'))
    subreddit = db.relationship('Subreddit', backref='posts')

    user_id = db.Column(db.ForeignKey('user.id'))
    user = db.relationship('User', backref='posts')

    @property
    def display_url(self):
        if self.url:
            return self.url
        return self.comments_url

    @property
    def score(self):
        return redis_store.hget(self.redis_key, "score") or 0

    @property
    def comments_url(self):
        return url_for('main.post', name=self.subreddit_name, post_id=self.id)

    @property
    def redis_key(self):
        return "p{}".format(self.id)

    def vote_status(self):
        return int(redis_store.hget(self.redis_key, current_user.id) or 2)

    def vote(self, direction):
        redis_store.vote_cmd(keys=(), args=(self.redis_key, current_user.id, int(direction == "up")))


class Comment(base):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String, unique=True)
    text = db.Column(db.Unicode())
    score = db.Column(db.Integer)

    user_id = db.Column(db.ForeignKey('user.id'))
    user = db.relationship('User', backref='comments')

    subcomments = db.relationship(
        'Comment',
        primaryjoin=remote(foreign(path)).like(path.concat('/%')),
        viewonly=True,
        order_by=path)
