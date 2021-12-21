web: gunicorn processor.server:app
worker: celery -A processor worker -l debug --concurrency=4
fetcher: python -m scripts.queue_stories
