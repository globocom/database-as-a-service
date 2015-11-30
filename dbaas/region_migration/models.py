# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db import models
from django.utils.translation import ugettext_lazy as _
from logical.models import Database
from util.models import BaseModel
from .migration_steps import get_engine_steps
from celery.task import control
from django.db.models.signals import pre_delete
from django.dispatch import receiver

LOG = logging.getLogger(__name__)


class DatabaseRegionMigration(BaseModel):
    database = models.ForeignKey(Database, verbose_name=("Database"),
                                 null=False, unique=True, related_name="migration")
    current_step = models.PositiveSmallIntegerField(verbose_name=_("Current \
                                                    Step"), null=False,
                                                    blank=False, default=0)

    def __unicode__(self):
        return '{}'.format(self.database)

    def get_steps(self,):
        return get_engine_steps(self.database.engine_type)

    def get_current_step(self,):
        return self.get_steps()[self.current_step]

    def is_migration_finished(self,):
        current_step = self.current_step
        last_step = len(self.get_steps()) - 1
        return current_step == last_step

    @property
    def warning(self,):
        return self.get_current_step().warning

    def description(self,):
        return self.get_current_step().description

    description.short_description = 'Next Step'

    @property
    def status(self,):
        return self.get_current_step().status

    class Meta:
        permissions = (
            ("view_databaseregionmigration",
             "Can view database region migration"),
        )


class DatabaseRegionMigrationDetail(BaseModel):
    WAITING = 0
    RUNNING = 1
    SUCCESS = 2
    ROLLBACK = 3
    REVOKED = 4
    ERROR = 5

    MAINTENANCE_STATUS = (
        (SUCCESS, 'Success'),
        (RUNNING, 'Running'),
        (WAITING, 'Waiting'),
        (ROLLBACK, 'Rollback'),
        (REVOKED, 'Revoked')
    )
    database_region_migration = models.ForeignKey(DatabaseRegionMigration,
                                                  related_name="details",
                                                  null=False)
    step = models.PositiveSmallIntegerField(verbose_name=_("Step"),
                                            null=False,
                                            blank=False)
    scheduled_for = models.DateTimeField(verbose_name=_("Schedule for"),
                                         null=False)
    started_at = models.DateTimeField(verbose_name=_("Started at"), null=True,
                                      blank=True)
    finished_at = models.DateTimeField(verbose_name=_("Finished at"),
                                       null=True, blank=True)
    created_by = models.CharField(verbose_name=_("Created by"), max_length=255,
                                  null=False, blank=False)
    revoked_by = models.CharField(verbose_name=_("Revoked by"), max_length=255,
                                  null=True, blank=True)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)
    log = models.TextField(verbose_name=_("Log"), null=False, blank=False)
    is_migration_up = models.BooleanField(verbose_name=_("Log"), default=True)
    celery_task_id = models.CharField(verbose_name=_("Celery task Id"),
                                      null=True, blank=False, max_length=50,)

    class Meta:
        unique_together = (
            ('database_region_migration', 'step', 'scheduled_for',)
        )
        permissions = (
            ("view_databaseregionmigrationdetail",
             "Can view database region migration detail"),
        )

    def __unicode__(self):
        return " Detail for %s" % (self.database_region_migration)

    def revoke_maintenance(self, request):
        if self.is_waiting_to_run:
            control.revoke(self.celery_task_id,)

            self.status = self.REVOKED
            self.revoked_by = request.user.username
            self.save()

        return True

    def is_waiting_to_run(self):
        if self.status != self.WAITING:
            LOG.info("Migration: {} has already run!".format(self))
            return False

        inspect = control.inspect()
        scheduled_tasks = inspect.scheduled()
        try:
            hosts = scheduled_tasks.keys()
        except Exception as e:
            LOG.info("Could not retrieve celery scheduled tasks: {}".format(e))
            return False

        for host in hosts:
            try:
                scheduled_tasks = scheduled_tasks[host]
            except TypeError:
                LOG.warn("There are no scheduled tasks")
                LOG.info(scheduled_tasks)
                continue

            for task in scheduled_tasks:
                if task['request']['id'] == self.celery_task_id:
                    return True

        return False


simple_audit.register(DatabaseRegionMigration, DatabaseRegionMigrationDetail)


@receiver(pre_delete, sender=DatabaseRegionMigrationDetail)
def region_migration_detail_pre_delete(sender, **kwargs):
    detail = kwargs.get("instance")
    LOG.debug("regionmigration pre-delete triggered")
    control.revoke(task_id=detail.celery_task_id)
