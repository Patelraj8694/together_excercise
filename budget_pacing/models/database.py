"""Flask-SQLAlchemy database instance.

Imported by models and by the application factory.  The ``db`` object is
bound to a Flask app via ``db.init_app(app)`` inside :func:`create_app`.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
