#celery worker -A app.celery &
gunicorn application:app --workers 1 --worker-class eventlet --log-file=- --log-level=DEBUG
