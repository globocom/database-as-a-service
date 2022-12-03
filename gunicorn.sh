#!/bin/sh

gunicorn --bind 0.0.0.0:$PORT --worker-class gevent --workers $WORKERS --log-file - host_provider.main:app