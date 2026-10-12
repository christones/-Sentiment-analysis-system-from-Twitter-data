"""Entry point for gunicorn:  gunicorn app.wsgi:app"""
from app.app import create_app

app = create_app()
