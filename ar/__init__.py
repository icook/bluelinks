import subprocess
import logging
import os
import yaml
import sys

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.assets import Environment, Bundle
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import Admin
from flask.ext.redis import FlaskRedis
from flask_mail import Mail
from jinja2 import FileSystemLoader


root = os.path.abspath(os.path.dirname(__file__) + '/../')
lm = LoginManager()
db = SQLAlchemy()
assets = Environment()
security = Security()
mail = Mail()
admin = Admin()
redis_store = FlaskRedis()


def create_app(config='/config.yml', log_level='INFO'):
    # initialize our flask application
    app = Flask(__name__, static_folder='../static', static_url_path='/static')

    # set our template path and configs
    app.jinja_loader = FileSystemLoader(os.path.join(root, 'templates'))
    config_vars = yaml.load(open(root + config))
    # inject all the yaml configs
    app.config.update(config_vars)
    # Remove the defaualt installed flask logger
    del app.logger.handlers[0]
    app.logger.setLevel(logging.NOTSET)
    log_format = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s]: %(message)s')
    log_level = getattr(logging, str(log_level), app.config['log_level'])

    logger = logging.getLogger()
    logger.setLevel(log_level)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(log_format)
    logger.addHandler(handler)

    # add the debug toolbar if we're in debug mode...
    if app.config['DEBUG']:
        class LoggerWriter:
            def __init__(self, logger, level):
                self.logger = logger
                self.level = level

            def write(self, message):
                if message != '\n':
                    self.logger.log(self.level, message)

            def flush(*args, **kwargs):
                pass

        sys.stdout = LoggerWriter(app.logger, logging.INFO)
        sys.stderr = LoggerWriter(app.logger, logging.INFO)

    # register all our plugins
    db.init_app(app)
    lm.init_app(app)
    admin.init_app(app)
    mail.init_app(app)
    redis_store.init_app(app)


    from . import models, forms, lua_redis
    redis_store.vote_cmd = redis_store.register_script(lua_redis.vote)

    user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security.init_app(app, user_datastore, confirm_register_form=forms.ExtendedRegisterForm)
    assets.init_app(app)
    # We're going to modify SCSS load path to let us override vanilla bootstrap stuff
    bootstrap_all = Bundle('../scss/main.scss',
                           filters=['scss'], output='gen/main.css')
    assets.register('bootstrap_all', bootstrap_all)

    hdlr = logging.FileHandler(app.config.get('log_file', 'webserver.log'))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    app.logger.addHandler(hdlr)
    app.logger.setLevel(logging.INFO)

    # try and fetch the git version information
    try:
        output = subprocess.check_output("git show -s --format='%ci %h'",
                                         shell=True).strip().rsplit(" ", 1)
        app.config['hash'] = output[1]
        app.config['revdate'] = output[0]
    # celery won't work with this, so set some default
    except Exception:
        app.config['hash'] = ''
        app.config['revdate'] = ''

    # Route registration
    # =========================================================================
    from . import views, models, api, admin_views as av
    app.register_blueprint(views.main)
    app.register_blueprint(api.api_bp, url_prefix='/api')

    admin.add_view(av.SubredditModelView(models.Subreddit, db.session))
    admin.add_view(av.BaseModelView(models.Comment, db.session))
    admin.add_view(av.BaseModelView(models.Post, db.session))

    return app
