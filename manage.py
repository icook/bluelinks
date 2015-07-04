import os

from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from ar import create_app, db

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)

root = os.path.abspath(os.path.dirname(__file__) + '/../')

from ar.models import User
from flask import current_app, _request_ctx_stack


@manager.option('-g', '--generate', default=False, action='store_true',
                help='makes a user account when regenerating')
def init_db(generate=False):
    """ Resets entire database to empty state """
    with app.app_context():
        db.session.commit()
        db.drop_all()
        db.create_all()
        if generate:
            u = User(email='admin')
            u.password = 'testing'
            db.session.add(u)
            db.session.commit()


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
