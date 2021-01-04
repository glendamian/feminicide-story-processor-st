web: gunicorn processor.server:app
worker: celery -A processor worker -l info
