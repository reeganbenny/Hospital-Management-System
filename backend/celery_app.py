"""Celery application for async and scheduled jobs."""
from celery import Celery
from celery.schedules import crontab
from config import Config

def make_celery(app=None):
    celery = Celery(
        app.import_name if app else "hms",
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=["tasks.reminders", "tasks.reports", "tasks.exports"],
    )
    if app:
        # Use new-style config keys only (Celery 5 rejects CELERY_* keys)
        celery.conf.update(
            broker_url=Config.CELERY_BROKER_URL,
            result_backend=Config.CELERY_RESULT_BACKEND,
        )
        celery.conf.beat_schedule = {
            "daily-reminders": {
                "task": "tasks.reminders.send_daily_reminders",
                "schedule": crontab(hour=Config.REMINDER_HOUR, minute=Config.REMINDER_MINUTE),
            },
            "monthly-doctor-reports": {
                "task": "tasks.reports.send_monthly_doctor_reports",
                "schedule": crontab(day_of_month=1, hour=9, minute=0),
            },
        }
    return celery
