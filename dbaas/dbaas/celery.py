from __future__ import absolute_import

import os
import logging
from datetime import timedelta

from celery import Celery

from django.conf import settings
from dbaas import celeryconfig

from logging.handlers import SysLogHandler
from celery.log import redirect_stdouts_to_logger

from celery.signals import after_setup_task_logger, after_setup_logger


def setup_log(**args):
    # redirect stdout and stderr to logger
    redirect_stdouts_to_logger(args['logger'])
    # logs to local syslog
    #syslog = SysLogHandler(address=settings.SYSLOG_FILE, facility=logging.handlers.SysLogHandler.LOG_LOCAL3)
    syslog = SysLogHandler(
        address=settings.SYSLOG_FILE, facility=logging.handlers.SysLogHandler.LOG_LOCAL3)
    # setting log level
    syslog.setLevel(args['loglevel'])
    # setting log format
    formatter = logging.Formatter('dbaas: #celery %(name)s %(message)s')
    syslog.setFormatter(formatter)
    # add new handler to logger
    args['logger'].addHandler(syslog)

# after_setup_logger.connect(setup_log)
# after_setup_task_logger.connect(setup_log)

LOG = logging.getLogger(__name__)

# set this variable to True to run celery tasks synchronously

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbaas.settings')

app = Celery('dbaas')

app.config_from_object(celeryconfig)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    LOG.debug('Request: {0!r}'.format(self.request))
