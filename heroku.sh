celery worker -A app.celery &
gunicorn app:app --worker 1 --worker-class eventlet --log-file=- --log-level=DEBUG
