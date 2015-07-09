import os
import datetime

from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from ar import create_app, db, redis_store

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)

root = os.path.abspath(os.path.dirname(__file__) + '/../')

from ar.models import User, Role, Community, Post, Comment
from ar.hot import hot
from flask import current_app, _request_ctx_stack


@manager.option('-g', '--generate', default=True, action='store_true',
                help='makes a user account when regenerating')
def init_db(generate=False):
    """ Resets entire database to empty state """
    with app.app_context():
        db.session.commit()
        db.drop_all()
        db.create_all()
        if generate:
            r = Role(name='admin', description='access to flask-admin')
            db.session.add(r)

            u = User(email='admin@localhost', username='admin')
            u.password = 'testing'
            u.active = True
            u.confirmed_at = datetime.datetime.utcnow()
            u.roles.append(r)
            db.session.add(u)

            for comm in ["pics", "funny", "videos", "news", "science"]:
                s = Community(name=comm, user=u)
                db.session.add(s)
                db.session.commit()
            print("Made an admin with username 'admin' and password 'testing'")


@manager.command
def update_hot():
    """ Setup a coinserver connection fot the shell context """
    # Make a hot zset for post comments
    for post in Post.query:
        query = Comment.query.filter_by(post_id=post.id).options(db.load_only("id", "created_at"))
        times = {c.id: c.created_at for c in query}
        hot_list = []
        for id, score in redis_store.zrange("pc{}".format(post.id), 0, -1, withscores=True):
            hot_list.extend((id, hot(score, times[int(id)])))
        if hot_list:
            redis_store.zadd("pch{}".format(post.id), *hot_list)
        print("Updated hot scores for post {:,}".format(post.id))

    # Make a hot zset for posts in subreddits
    for comm in Community.query:
        query = Post.query.filter_by(community_name=comm.name).options(db.load_only("id", "created_at"))
        times = {c.id: c.created_at for c in query}
        hot_list = []
        for id, score in redis_store.zrange("{}".format(comm.name), 0, -1, withscores=True):
            hot_list.extend((id, hot(score, times[int(id)])))
        if hot_list:
            redis_store.zadd("h{}".format(comm.name), *hot_list)
        print("Updated hot scores for community {}".format(comm.name))


def make_context():
    """ Setup a coinserver connection fot the shell context """
    app = _request_ctx_stack.top.app
    return dict(app=app)
manager.add_command("shell", Shell(make_context=make_context))
manager.add_command('db', MigrateCommand)


@manager.command
def runserver():
    current_app.run(debug=True, host='0.0.0.0')


if __name__ == "__main__":
    manager.run()
