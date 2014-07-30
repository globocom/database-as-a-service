# -*- coding: utf-8 -*-

from dbaas.celery import app
from util.decorators import only_one
from models import CeleryHealthCheck
#from celery.utils.log import get_task_logger

#LOG = get_task_logger(__name__)

import logging
LOG = logging.getLogger(__name__)



@app.task(bind=True)
def set_celery_healthcheck_last_update(self):
    
    LOG.info("Setting Celery healthcheck last update")
    CeleryHealthCheck.set_last_update()
    
    return