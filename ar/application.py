import subprocess
import logging
import os
import yaml
import sys
import inspect

from flask import Flask, current_app, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.assets import Environment, Bundle
from flask.ext.security import Security
from flask.ext.admin import Admin
from flask.ext.redis import FlaskRedis
from flask.ext.misaka import Misaka
from flask.ext.celery import Celery
from flask_mail import Mail
from jinja2 import FileSystemLoader
from werkzeug.local import LocalProxy

import ar.filters as filters
import pyximport
from ar.renderers import LinkRenderer

pyximport.install()


root = os.path.abspath(os.path.dirname(__file__) + '/../')
security = LocalProxy(lambda: current_app.extensions['security'])
lm = LoginManager()
db = SQLAlchemy()
assets = Environment()
_security = Security()
mail = Mail()
admin = Admin()
redis_store = FlaskRedis()
celery = Celery()
md_renderer = LinkRenderer()
md = Misaka(renderer=md_renderer, no_html=True, no_images=True,
            autolink=True, fenced_code=True, space_headers=True,
            no_intra_emphasis=True, strikethrough=True, superscript=True)


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

    # register all our plugins
    db.init_app(app)
    lm.init_app(app)
    admin.init_app(app)
    mail.init_app(app)
    redis_store.init_app(app)
    md.init_app(app)
    celery.init_app(app)

    from . import models, forms, lua_redis
    redis_store.vote_cmd = redis_store.register_script(lua_redis.vote)

    from . import admin_views as av
    user_datastore = av.SQLAlchemyUserDatastoreCustom(db, models.User, models.Role)
    _security.init_app(app, user_datastore, register_form=forms.ExtendedRegisterForm)
    app.extensions['security'].login_form = forms.LoginForm
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
                                         shell=True).decode('utf8').strip().rsplit(" ", 1)
        app.config['hash'] = output[1]
        app.config['revdate'] = output[0]
    # celery won't work with this, so set some default
    except Exception:
        app.logger.debug("unable to grab git information", exc_info=True)
        app.config['hash'] = ''
        app.config['revdate'] = ''

    # Dynamically add all the filters in the filters.py file
    for name, func in inspect.getmembers(filters, inspect.isfunction):
        app.jinja_env.filters[name] = func

    # Route registration
    # =========================================================================
    from . import views, models, api, admin_views as av
    app.register_blueprint(views.main)
    app.register_blueprint(api.api_bp, url_prefix='/api')

    admin.add_view(av.CommunityModelView(models.Community, db.session))
    admin.add_view(av.BaseModelView(models.Comment, db.session))
    admin.add_view(av.PostModelView(models.Post, db.session))
    admin.add_view(av.BaseModelView(models.User, db.session))

    @app.errorhandler(500)
    def handle_err_500(error):
        current_app.logger.exception(error)
        return render_template("errors/_500.html", no_header=True)

    @app.errorhandler(404)
    def handle_err_404(error):
        current_app.logger.exception(request.url)
        return render_template("errors/_404.html", no_header=True)

    @app.errorhandler(403)
    def handle_err_403(error):
        current_app.logger.exception(error)
        return render_template("errors/_403.html", no_header=True)

    return app
