from __future__ import absolute_import

import os
import logging
from datetime import timedelta

from celery import Celery

from django.conf import settings

LOG = logging.getLogger(__name__)

BROKER_URL = os.getenv('DBAAS_NOTIFICATION_BROKER_URL', 'redis://localhost:6379/0')

#set this variable to True to run celery tasks synchronously
CELERY_ALWAYS_EAGER = False

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbaas.settings')

app = Celery('dbaas')

app.conf.update(
    CELERY_TRACK_STARTED=True,
)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    LOG.debug('Request: {0!r}'.format(self.request))