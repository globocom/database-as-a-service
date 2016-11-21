# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson
from logical.models import Database

from util.models import BaseModel

LOG = logging.getLogger(__name__)


class TaskHistory(BaseModel):

    class Meta:
        verbose_name_plural = "Task histories"

    STATUS_PENDING = 'PENDING'
    STATUS_RUNNING = 'RUNNING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_ERROR = 'ERROR'
    STATUS_WARNING = 'WARNING'
    STATUS_WAITING = 'WAITING'

    _STATUS = [STATUS_PENDING, STATUS_RUNNING, STATUS_SUCCESS,
               STATUS_ERROR, STATUS_WARNING, STATUS_WAITING]

    task_id = models.CharField(
        _('Task ID'), max_length=200, null=True, blank=True, editable=False)
    task_name = models.CharField(
        _('Task Name'), max_length=200, null=True, blank=True)
    user = models.CharField(max_length=255, null=True, blank=True)
    ended_at = models.DateTimeField(
        verbose_name=_("Ended at"), null=True, blank=True, editable=False)
    task_status = models.CharField(
        _('Task Status'), max_length=100, default=STATUS_PENDING)
    context = models.TextField(null=True, blank=True)
    details = models.TextField(
        verbose_name=_("Details"), null=True, blank=True)
    arguments = models.TextField(
        verbose_name=_("Arguments"), null=True, blank=True)
    db_id = models.ForeignKey(
        Database, related_name="database", null=True, blank=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return u"%s" % self.task_id

    def load_context_data(self):
        if self.context == '':
            self.context = '{}'
        self.context_data = simplejson.loads(self.context)
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
        self.db_id = db
        self.save()

    def update_ended_at(self):
        self.ended_at = datetime.now()
        self.save()

    @classmethod
    def register(cls, request=None, user=None, task_history=None, worker_name=None):

        LOG.info("task id: %s | task name: %s | " % (request.id,
                                                     request.task))

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

        if request.task == 'notification.tasks.create_database':
            task_history.arguments = "Database name: {0},\nEnvironment: {1},\
            \nProject: {2},\nPlan: {3}".format(
                request.kwargs['name'], request.kwargs['environment'],
                request.kwargs['project'], request.kwargs['plan'])

        elif request.task == 'notification.tasks.resize_database':
            task_history.arguments = "Database name: {0},\nNew Offering: {1}".format(
                request.kwargs['database'].name, request.kwargs['cloudstackpack'])

        elif request.task == 'notification.tasks.database_disk_resize':
            task_history.arguments = \
                "Database name: {0}," \
                "\nNew Disk Offering: {1}".format(
                    request.kwargs['database'].name,
                    request.kwargs['disk_offering']
                )

        elif request.task == 'backup.tasks.restore_snapshot':
            task_history.arguments = "Restoring to an older version the database: {0}, it will finish soon.".format(
                request.kwargs['database'].name)

        elif request.task == 'notification.tasks.destroy_database':
            task_history.arguments = "Database name: {0},\nUser: {1}".format(
                request.kwargs['database'].name, request.kwargs['user'])

        elif request.task == 'notification.tasks.clone_database':
            task_history.arguments = "Database name: {0},\nClone: {1},\nPlan: {2},\
            \nEnvironment: {3}".format(
                request.kwargs['origin_database'].name, str(
                    request.kwargs['clone_name']),
                str(request.kwargs['plan']), str(request.kwargs['environment']))

        elif request.task == 'dbaas_services.analyzing.tasks.analyze.analyze_databases':
            task_history.arguments = "Analizing all databases"

        elif request.task == 'notification.tasks.upgrade_mongodb_24_to_30':
            task_history.arguments = "Upgrading database {0}, to MongoDB 3.0".format(
                request.kwargs['database'].name,)

        elif request.task == 'dbaas_aclapi.tasks.unbind_address_on_database':
            task_history.arguments = "Removing binds for {0} from {1}".format(
                request.kwargs['database_bind'],
                request.kwargs['database_bind'].database)

        elif request.task == 'dbaas_aclapi.tasks.bind_address_on_database':
            task_history.arguments = "Creating binds for {0} from {1}".format(
                request.kwargs['database_bind'],
                request.kwargs['database_bind'].database)

        else:
            task_history.arguments = request.args

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
