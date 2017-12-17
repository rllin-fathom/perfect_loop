celery worker -A app.celery &
gunicorn app:app --worker-class eventlet --log-file=- --log-level=DEBUG
