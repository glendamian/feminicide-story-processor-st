#!/bin/sh
celery -A processor worker -l info --concurrency=4
