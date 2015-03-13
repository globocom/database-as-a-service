# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db import models
from django.utils.translation import ugettext_lazy as _
from physical.models import Host
from util.models import BaseModel
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from celery.task import control
from .tasks import execute_scheduled_maintenance

LOG = logging.getLogger(__name__)


class Maintenance(BaseModel):
    WAITING = 0
    RUNNING = 1
    FINISHED = 2
    REJECTED = 3

    MAINTENANCE_STATUS = (
        (FINISHED, 'Finished'),
        (RUNNING, 'Running'),
        (WAITING, 'Waiting'),
        (REJECTED, 'Rejected'),
    )

    description = models.CharField(verbose_name=_("Description"),
        null=False, blank=False, max_length=500,)
    scheduled_for = models.DateTimeField(verbose_name=_("Schedule for"),
        unique=True,)
    main_script = models.TextField(verbose_name=_("Main Script"),
        null=False, blank=False)
    rollback_script = models.TextField(verbose_name=_("Rollback Script"),
        null=True, blank=True)
    host_query = models.TextField(verbose_name=_("Query Hosts"),
        null=False, blank=False)
    maximum_workers = models.PositiveSmallIntegerField(verbose_name=_("Maximum workers"),
        null=False, default=1)
    celery_task_id = models.CharField(verbose_name=_("Celery task Id"),
        null=True, blank=True, max_length=50,)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)

    def __unicode__(self):
       return "%s" % self.description

    def save_host_maintenance(self,):
        hosts = Host.objects.raw(self.host_query)
        try:
            for host in hosts:
                hm = HostMaintenance()
                hm.host = host
                hm.maintenance = self
                hm.save()
        except Exception, e:
            LOG.warn("There is something wrong with the given query")
            LOG.warn("Error: {}".format(e.args[1]))
            self.status = self.REJECTED

            # post_save signal has to be disconnected in order to avoid
            # recursive signal call
            post_save.disconnect(maintenance_post_save, sender=Maintenance)

            self.save()
            # connecting signal again
            post_save.connect(maintenance_post_save, sender=Maintenance)
            return False

        return True

    def is_waiting_to_run(self):
        if self.status == self.FINISHED:
            LOG.info("Maintenance: {} has already run!".format(self))
            return False

        inspect = control.inspect()
        scheduled_tasks = inspect.scheduled()
        hosts = scheduled_tasks.keys()

        for host in hosts:
            try:
                scheduled_tasks = scheduled_tasks[host]
            except TypeError:
                LOG.warn("There are no scheduled tasks")
                LOG.info(scheduled_tasks)
                return False

            for task in scheduled_tasks:
                if  task['id'] == self.celery_task_id:
                    return True

        return False



class HostMaintenance(BaseModel):
    ERROR = 0
    SUCCESS = 1
    RUNNING = 2
    ROLLBACK = 3
    WAITING = 4
    ROLLBACK_ERROR = 5
    ROLLBACK_SUCCESS = 6

    MAINTENANCE_STATUS = (
        (ERROR, 'Error'),
        (SUCCESS, 'Success'),
        (RUNNING, 'Running'),
        (ROLLBACK, 'Rollback'),
        (WAITING, 'Waiting'),
        (ROLLBACK_ERROR, 'Rollback error'),
        (ROLLBACK_SUCCESS, 'Rollback success'),
    )

    started_at = models.DateTimeField(verbose_name=_("Started at"), null=True)
    finished_at = models.DateTimeField(verbose_name=_("Finished at"),null=True)
    main_log = models.TextField(verbose_name=_("Main Script"),
        null=True, blank=True)
    rollback_log = models.TextField(verbose_name=_("Rollback Script"),
        null=True, blank=True)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)
    host = models.ForeignKey(Host, related_name="host_maintenance",)
    maintenance = models.ForeignKey(Maintenance, related_name="maintenance",)

    class Meta:
        unique_together = (("host", "maintenance"),)
        index_together = [["host", "maintenance"],]

    def __unicode__(self):
        return "%s %s" % (self.host, self.maintenance)

simple_audit.register(Maintenance)
simple_audit.register(HostMaintenance)



#########
# SIGNALS#
#########

@receiver(pre_delete, sender=Maintenance)
def database_pre_delete(sender, **kwargs):
    """
    maintenance pre delete signal. Revoke scheduled task and remove
    its HostMaintenance objects
    """
    maintenance = kwargs.get("instance")
    LOG.debug("maintenance pre-delete triggered")
    HostMaintenance.objects.filter().delete()
    control.revoke(task_id=maintenance.celery_task_id)



@receiver(post_save, sender=Maintenance)
def maintenance_post_save(sender, **kwargs):
    """
     maintenance post save signal. Creates the maintenance
     task on celery and its HostMaintenance objetcs.
    """
    maintenance = kwargs.get("instance")
    is_new = kwargs.get("created")
    LOG.debug("maintenance post-save triggered")

    if is_new or not maintenance.celery_task_id:
        LOG.info("Spawning task and HostMaintenance objects...")

        if maintenance.save_host_maintenance():
            task = execute_scheduled_maintenance.apply_async(args=[maintenance],
                eta=maintenance.scheduled_for)

            maintenance.celery_task_id = task.task_id
            maintenance.save()
