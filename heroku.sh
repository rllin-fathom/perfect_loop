celery worker -A app.celery &
gunicorn app:app --log-file=- --log-level=DEBUG
