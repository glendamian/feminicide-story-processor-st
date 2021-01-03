#!/bin/sh
gunicorn processor.server:app
