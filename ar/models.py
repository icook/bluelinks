import datetime

from sqlalchemy.orm import remote, foreign
from flask.ext.security import UserMixin, RoleMixin
from flask.ext.login import current_user
from flask import url_for
from .model_lib import base
from .application import db, redis_store


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


user_subscriptions = db.Table('user_subscriptions',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('community_name', db.String(), db.ForeignKey('community.name')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(base, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    subscriptions = db.relationship("Community",
                                    secondary=user_subscriptions)

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

    def __str__(self):
        return "/u/{}".format(self.username)

    @property
    def message_count(self):
        return self.messages.count()


class Community(base):
    name = db.Column(db.String, primary_key=True)

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='communities')

    def __str__(self):
        return "/c/{}".format(self.name)


class Post(base):
    id = db.Column(db.Integer, primary_key=True)
    # Either url or text, not both...
    url = db.Column(db.String)
    text = db.Column(db.Unicode)
    title = db.Column(db.Unicode, nullable=False)
    thumbnail_path = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    community_name = db.Column(db.ForeignKey('community.name'))
    community = db.relationship('Community', backref='posts')

    username = db.Column(db.ForeignKey('user.username'))
    user = db.relationship('User', backref='posts')

    type = "p"

    @property
    def display_url(self):
        if self.url:
            return self.url
        return self.comments_url

    @property
    def comment_count(self):
        return Comment.query.filter_by(post_id=self.id).count()

    @property
    def score(self):
        return int(redis_store.zscore(self.community_name, self.id) or 0)

    @property
    def comments_url(self):
        return url_for('main.post', name=self.community_name, post_id=self.id)

    @property
    def redis_key(self):
        return "p{}".format(self.id)

    @property
    def group(self):
        return self.community_name

    def vote_status(self):
        return int(redis_store.hget(self.redis_key, current_user.id) or 2)


class Comment(base):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String, unique=True)
    text = db.Column(db.Unicode, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    post_id = db.Column(db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('comments', order_by=path))

    username = db.Column(db.ForeignKey('user.username'), nullable=False)
    user = db.relationship('User', backref='comments')

    type = "c"

    subcomments = db.relationship(
        'Comment',
        primaryjoin=remote(foreign(path)).like(path.concat('/%')),
        viewonly=True,
        order_by=path)

    @property
    def redis_key(self):
        return "c{}".format(self.id)

    @property
    def group(self):
        return self.post_id

    def vote_status(self):
        return int(redis_store.hget(self.redis_key, current_user.id) or 2)

    @property
    def score(self):
        return int(redis_store.zscore("pc{}".format(self.post_id), self.id) or 0)


class Message(base):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Unicode)
    subject = db.Column(db.Unicode, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    # Sending user
    from_username = db.Column(db.ForeignKey('user.username'))
    from_user = db.relationship('User', foreign_keys=[from_username], backref='sent_messages')

    # Receiving user
    to_username = db.Column(db.ForeignKey('user.username'))
    to_user = db.relationship('User', foreign_keys=[to_username], backref='messages')

    # marked for deletion. Keep archived for records
    deleted = db.Column(db.Boolean, default=False)