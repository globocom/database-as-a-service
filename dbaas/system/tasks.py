# -*- coding: utf-8 -*-
from dbaas.celery import app
from util.decorators import only_one
from models import CeleryHealthCheck
from notification.models import TaskHistory

import logging
LOG = logging.getLogger(__name__)



@app.task(bind=True)
@only_one(key="celery_healthcheck_last_update", timeout=20)
def set_celery_healthcheck_last_update(self):
    try:
        task_history = TaskHistory.register(request=self.request, user=None)

        LOG.info("Setting Celery healthcheck last update")
        CeleryHealthCheck.set_last_update()

        task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details="Finished")
    except Exception, e:
        LOG.warn("Oopss...{}".format(e))
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)
    finally:
        return
