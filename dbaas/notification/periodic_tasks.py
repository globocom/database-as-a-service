from __future__ import absolute_import
from celery.utils.log import get_task_logger
from datetime import date, timedelta

from dbaas.celery import app
from physical.models import DatabaseInfra, Instance
from util import email_notifications, get_worker_name, full_stack
from notification.models import TaskHistory
from maintenance.models import TaskSchedule


LOG = get_task_logger(__name__)


@app.task(bind=True)
def check_ssl_expire_at(self):
    LOG.info("Retrieving all SSL MySQL databases")
    worker_name = get_worker_name()
    task = TaskHistory.register(
        request=self.request, user=None, worker_name=worker_name)
    task.relevance = TaskHistory.RELEVANCE_CRITICAL

    one_month_later = date.today() + timedelta(days=30)
    try:
        infras = DatabaseInfra.objects.filter(
            ssl_configured=True,
            engine__engine_type__name='mysql',
            instances__hostname__ssl_expire_at__lte=one_month_later
        ).distinct()
        for infra in infras:
            database = infra.databases.first()
            task.update_details(
                "Checking database {}...".format(database), persist=True
            )
            scheudled_tasks = TaskSchedule.objects.filter(
                scheduled_for__lte=one_month_later,
                status=TaskSchedule.SCHEDULED,
                database=database
            )
            if scheudled_tasks:
                task.update_details("Already scheduled!\n", persist=True)
            else:
                TaskSchedule.objects.create(
                    method_path='ddd',
                    scheduled_for=one_month_later,
                    database=database
                )
                task.update_details("Schedule created!\n", persist=True)
        task.update_status_for(TaskHistory.STATUS_SUCCESS, details="\nDone")
    except Exception as err:
        task.update_status_for(TaskHistory.STATUS_ERROR, details=err)
        return
