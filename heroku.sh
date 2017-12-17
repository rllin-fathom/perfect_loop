#web: gunicorn app:app --log-file=- --log-level=DEBUG
celery worker -A app.celery &
gunicorn app:app --log-file=- --log-level=DEBUG
