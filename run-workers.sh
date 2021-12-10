#!/bin/sh
celery -A processor worker -l debug --concurrency=4
