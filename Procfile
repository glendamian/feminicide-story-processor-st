web: gunicorn -w 4 -k gevent --timeout 500 processor.server:app
worker: celery -A processor worker -l info --concurrency=4
fetcher-mc: python -m scripts.queue_mediacloud_stories
fetcher-ga: python -m scripts.queue_googlealerts_stories
