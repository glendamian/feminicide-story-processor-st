#!/bin/sh
gunicorn -w 4 -k gevent --timeout 500 processor.server:app
