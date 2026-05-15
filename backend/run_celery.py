"""Celery worker entry point. Run from backend/: celery -A run_celery.celery worker -l info
   Beat: celery -A run_celery.celery beat -l info"""
from app import create_app
from celery_app import make_celery

app = create_app()
celery = make_celery(app)
celery.flask_app = app