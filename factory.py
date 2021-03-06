from __future__ import absolute_import
import os
import time
import uuid
from datetime import datetime
import logging
from logging.handlers import SMTPHandler

from flask import (Flask, abort, g, request, session, render_template,
                   current_app)
from flask.ext.babel import get_locale as babel_locale
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.utils import import_string

from flamaster.account import user_ds, connection_ds
from flamaster.core import http
from flamaster.core.session import RedisSessionInterface
from flamaster.extensions import register_jinja_helpers


class ExtensionLoadError(Exception):
    pass


class BlueprintLoadError(Exception):
    pass


class AppFactory(object):
    """ Application factory for creating flask instance serving this project.
        Usage:
            app = AppFactory('settings').init_app(__name__)
    """

    def __init__(self, config, envvar='PROJECT_SETTINGS', bind_db_object=True):
        self.app_config = config
        self.app_envvar = os.environ.get(envvar, False)
        # self.bind_db_object = bind_db_object

    def init_app(self, app_name, **kwargs):
        app = Flask(app_name, **kwargs)
        app.config.from_object(self.app_config)
        app.config.from_envvar(self.app_envvar, silent=True)

        self._add_logger(app)
        self._bind_extensions(app)
        self._register_blueprints(app)
        self._register_hooks(app)

        app.session_interface = RedisSessionInterface()
        app.wsgi_app = ProxyFix(app.wsgi_app)
        return app

    def _import(self, path):
        module_name, object_name = path.rsplit('.', 1)
        module = import_string(module_name)
        return module, object_name

    def _bind_extensions(self, app):
        for ext_path in app.config.get('EXTENSIONS', []):
            module, ext_name = self._import(ext_path)

            try:
                ext = getattr(module, ext_name)
            except AttributeError:
                ExtensionLoadError("Extension '{}'' not found".format(ext))

            try:
                # TODO: create workaround for special cases
                if ext_name == 'security':
                    ext.init_app(app, datastore=user_ds)
                elif ext_name == 'social':
                    ext.init_app(app, datastore=connection_ds)
                else:
                    ext.init_app(app)

            except AttributeError:
                ext(app)

    def _register_blueprints(self, app):
        """ Register all blueprint modules listed under the settings
            BLUEPRINTS key """
        for blueprint_path in app.config.get('BLUEPRINTS', []):
            module, bp_name = self._import(blueprint_path)
            if hasattr(module, bp_name):
                app.register_blueprint(getattr(module, bp_name))
            else:
                raise BlueprintLoadError('No {} blueprint '
                                         'found'.format(bp_name))

    def _register_hooks(self, app):
        register_jinja_helpers(app)
        app.before_request(setup_session)
        app.errorhandler(http.NOT_FOUND)(show_page_not_found)
        app.errorhandler(http.INTERNAL_ERR)(show_internal_error)
        app.after_request(modify_headers)
        app.extensions['babel'].localeselector(get_locale(app))

    def _add_logger(self, app):
        """ Creates SMTPHandler for logging errors to the specified admins list
        """
        kwargs = dict()
        username = app.config.get('MAIL_USERNAME')
        password = app.config.get('MAIL_PASSWORD')

        if username and password:
            kwargs['credentials'] = (username, password)

        mail_handler = SMTPHandler(app.config['MAIL_SERVER'],
                                   app.config['DEFAULT_MAIL_SENDER'],
                                   app.config['ADMINS'],
                                   '[ERROR] Findevent got error',
                                   **kwargs)

        mail_handler.setFormatter(logging.Formatter('''
            Message type:       %(levelname)s
            Location:           %(pathname)s:%(lineno)d
            Module:             %(module)s
            Function:           %(funcName)s
            Time:               %(asctime)s

            Message:

            %(message)s
        '''))

        mail_handler.setLevel(logging.DEBUG)

        if not app.debug:
            app.logger.addHandler(mail_handler)


def modify_headers(response):
    map(lambda h: response.headers.add(*h), current_app.config['HEADERS'])
    return response


def setup_session():
    g.now = time.mktime(datetime.utcnow().timetuple())
    g.locale = babel_locale().language
    session['id'] = session.get('id', uuid.uuid4().hex)


def show_internal_error(error):
    return render_template('50x.html'), http.INTERNAL_ERR


def show_page_not_found(error):
    try:
        return render_template('base.html'), http.NOT_FOUND
    except:
        return abort(http.NOT_FOUND)


def get_locale(app):
    def closure():
        languages = app.config['ACCEPT_LANGUAGES']
        matched = request.accept_languages.best_match(languages)
        language = session.get(app.config['LOCALE_KEY'], matched)
        return language

    return closure
