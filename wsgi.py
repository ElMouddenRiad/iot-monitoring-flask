"""WSGI entrypoint for production deployment.

This module exposes the Flask application under both `app` and
`application` so it works with common WSGI servers such as Gunicorn or uWSGI.
"""

from app import app

application = app
