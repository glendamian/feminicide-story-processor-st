web: gunicorn processor.server:app
worker: celery -A processor worker -l debug
fetcher: python -m scripts.queue_stories
