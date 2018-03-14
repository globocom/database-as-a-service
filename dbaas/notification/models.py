# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import time
from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
import json
from django_redis import get_redis_connection

from util.models import BaseModel

LOG = logging.getLogger(__name__)


class TaskHistory(BaseModel):

    class Meta:
        verbose_name_plural = "Task histories"

    STATUS_RUNNING = 'RUNNING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_ERROR = 'ERROR'
    STATUS_WARNING = 'WARNING'
    STATUS_WAITING = 'WAITING'

    _STATUS = [STATUS_RUNNING, STATUS_SUCCESS,
               STATUS_ERROR, STATUS_WARNING, STATUS_WAITING]

    task_id = models.CharField(
        _('Task ID'), max_length=200, null=True, blank=True, editable=False
    )
    task_name = models.CharField(
        _('Task Name'), max_length=200, null=True, blank=True
    )
    user = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    ended_at = models.DateTimeField(
        verbose_name=_("Ended at"), null=True, blank=True, editable=False
    )
    task_status = models.CharField(
        _('Task Status'), max_length=100, default=STATUS_WAITING, db_index=True
    )
    context = models.TextField(null=True, blank=True)
    details = models.TextField(
        verbose_name=_("Details"), null=True, blank=True
    )
    arguments = models.TextField(
        verbose_name=_("Arguments"), null=True, blank=True
    )
    db_id = models.IntegerField(
        verbose_name=_("Database"), null=True, blank=True
    )
    object_id = models.IntegerField(null=True, blank=True)
    object_class = models.CharField(max_length=255, null=True, blank=True)
    database_name = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )

    def __unicode__(self):
        return u"%s" % self.task_id

    def load_context_data(self):
        if self.context == '':
            self.context = '{}'
        self.context_data = json.loads(self.context)
        return self.context_data

    def update_details(self, details, persist=False):
        """
        Method to update the details of a task history.
        TODO: should we put a timestamp in details? should we append the details?
        """

        if self.details:
            self.details = "\n%s%s" % (self.details, details)
        else:
            self.details = details

        if persist:
            self.save()

    def add_detail(self, message, level=None):
        extra = ''
        if level > 0:
            extra = '{}> '.format('-' * level)

        self.details = "{}\n".format(self.details) if self.details else ""
        self.details = '{}{}{}'.format(self.details, extra, message)
        self.save()

    def add_step(self, step, total, description):
        current_time = str(time.strftime("%m/%d/%Y %H:%M:%S"))
        message = '{} - Step {} of {} - {}'.format(
            current_time, step, total, description
        )
        self.add_detail(message, level=2)
        LOG.info(message)

    def update_status_for(self, status, details=None):
        if status not in TaskHistory._STATUS:
            raise RuntimeError("Invalid task status")

        self.task_status = status
        self.details = (self.details or " ") + "\n" + str(details)
        if status in [TaskHistory.STATUS_SUCCESS, TaskHistory.STATUS_ERROR, TaskHistory.STATUS_WARNING]:
            self.update_ended_at()
        else:
            self.save()

    def update_dbid(self, db):
        self.db_id = db.id
        self.save()

    def update_ended_at(self):
        self.ended_at = datetime.now()
        self.save()

    @classmethod
    def register(cls, request=None, user=None, task_history=None, worker_name=None):
        from .util import factory_arguments_for_task

        LOG.info(
            "task id: {} | task name: {} | ".format(request.id, request.task)
        )

        if not task_history:
            task_history = TaskHistory()

        if task_history.task_id:
            task_history.task_id += ';' + request.id
        else:
            task_history.task_id = request.id

        task_history.task_name = request.task
        task_history.task_status = TaskHistory.STATUS_RUNNING

        if task_history.context:
            task_history.context.update({"worker_name": worker_name})
        else:
            task_history.context = {"worker_name": worker_name}

        arguments = factory_arguments_for_task(request.task, request.kwargs)
        task_history.arguments = ", ".join(arguments)

        if user:
            task_history.user = str(user.username)

        task_history.save()

        return task_history

    @classmethod
    def running_tasks(cls):
        return cls.objects.filter(task_status=cls.STATUS_RUNNING)

    @classmethod
    def waiting_tasks(cls):
        return cls.objects.filter(task_status=cls.STATUS_WAITING)

    @property
    def is_running(self):
        return self.task_status == self.STATUS_RUNNING

    @property
    def is_status_error(self):
        return self.task_status == self.STATUS_ERROR

    def error_in_lock(self, database):
        self.add_detail("FAILED!")
        self.add_detail("Database {} is not allocated for this task.".format(
            database.name
        ))
        self.task_status = self.STATUS_ERROR
        self.save()

    def set_status_error(self, details=None, database_unpin=None):
        self._set_status(TaskHistory.STATUS_ERROR, details, database_unpin)

    def set_status_warning(self, details=None, database_unpin=None):
        self._set_status(TaskHistory.STATUS_WARNING, details, database_unpin)

    def set_status_success(self, details=None, database_unpin=None):
        self._set_status(TaskHistory.STATUS_SUCCESS, details, database_unpin)

    def _set_status(self, status, details, database_unpin):
        self.update_status_for(status, details)
        if database_unpin:
            database_unpin.finish_task()


###########
# SIGNALS #
###########


@receiver(post_save, sender=TaskHistory)
def save_task(sender, instance, **kwargs):
    user = instance.user
    if user:
        conn = get_redis_connection("notification")
        username = user if isinstance(user, basestring) else user.username
        key = "task_users:{}:{}".format(username, instance.id)
        params = {
            'task_id': instance.id,
            'task_name': instance.task_name.split('.')[-1],
            'task_status': instance.task_status,
            'user': username, 'arguments': instance.arguments,
            'database_name': instance.database_name or '',
            'updated_at': int(time.mktime(instance.updated_at.timetuple())),
            'is_new': 1,
            'read': 0
        }

        old_value = conn.hgetall(key)
        if old_value and params.get('task_status') == old_value.get('task_status'):
                params['is_new'] = old_value['is_new']
                params['read'] = old_value['read']

        conn.hmset(key, params)
        conn.expire(key, 1200)
