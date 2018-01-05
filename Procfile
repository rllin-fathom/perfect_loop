redis: redis-server
celery: celery -A application.celery worker -c 4 --loglevel=info
web: gunicorn application:app -b 0.0.0.0:5000 --workers 1 --worker-class eventlet --log-file=- --log-level=DEBUG
