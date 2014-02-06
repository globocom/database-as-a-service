from __future__ import absolute_import

import os
import logging
from datetime import timedelta

from celery import Celery

from django.conf import settings
from dbaas import celeryconfig

LOG = logging.getLogger(__name__)

#set this variable to True to run celery tasks synchronously

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbaas.settings')

app = Celery('dbaas')

app.config_from_object(celeryconfig)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    LOG.debug('Request: {0!r}'.format(self.request))