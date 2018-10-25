import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask

from deviceNanny.config import Config


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, 'deviceNanny.sqlite')
    )
    app.config.from_object(config_class)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/devicenanny.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Device Nanny startup')

    from . import db
    db.init_app(app)
    db.load_settings(app)

    # Home page
    from . import home
    app.register_blueprint(home.bp)

    # Add user page
    from . import user
    app.register_blueprint(user.bp)

    # Add devices page
    from . import devices
    app.register_blueprint(devices.bp)

    # Add settings page
    from . import settings
    app.register_blueprint(settings.bp)

    # Add api endpoint
    from . import api
    app.register_blueprint(api.bp)

    return app
