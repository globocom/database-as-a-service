#!/bin/sh

# gunicorn --bind 0.0.0.0:$PORT --workers $WORKERS --log-file - host_provider.main:app


cd /home/app/dbaas
gunicorn dbaas.wsgi \
    --bind 0.0.0.0:$PORT \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --log-level=$DEBUG_LEVEL
    

# python manage.py run_gunicorn
# python manage.py runserver 0.0.0.0:8000
