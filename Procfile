web: gunicorn processor.server:app
worker: celery -A processor worker -l info
fetcher: python -m scripts.queue_stories
