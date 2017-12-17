celery worker -A app.celery &
gunicorn -k eventlet app:app --log-file=- --log-level=DEBUG
