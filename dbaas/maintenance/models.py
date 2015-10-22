# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db import models
from django.utils.translation import ugettext_lazy as _
from dateutil import tz
from datetime import datetime
from physical.models import Host
from util.models import BaseModel
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from celery.task import control
from maintenance.tasks import execute_scheduled_maintenance
from .registered_functions.functools import _get_registered_functions
LOG = logging.getLogger(__name__)


class Maintenance(BaseModel):
    WAITING = 0
    RUNNING = 1
    FINISHED = 2
    REJECTED = 3
    REVOKED = 4

    MAINTENANCE_STATUS = (
        (FINISHED, 'Finished'),
        (RUNNING, 'Running'),
        (WAITING, 'Waiting'),
        (REJECTED, 'Rejected'),
        (REVOKED, 'Revoked')
    )

    description = models.CharField(verbose_name=_("Description"),
                                   null=False, blank=False, max_length=500,)
    scheduled_for = models.DateTimeField(verbose_name=_("Schedule for"),
                                         unique=True,)
    main_script = models.TextField(verbose_name=_("Main Script"),
                                   null=False, blank=False)
    rollback_script = models.TextField(verbose_name=_("Rollback Script"),
                                       null=True, blank=True)
    maximum_workers = models.PositiveSmallIntegerField(verbose_name=_("Maximum workers"),
                                                       null=False, default=1)
    celery_task_id = models.CharField(verbose_name=_("Celery task Id"),
                                      null=True, blank=True, max_length=50,)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)
    affected_hosts = models.IntegerField(
        verbose_name=_("Affected hosts"), default=0)
    started_at = models.DateTimeField(
        verbose_name=_("Started at"), null=True, blank=True)
    finished_at = models.DateTimeField(
        verbose_name=_("Finished at"), null=True, blank=True)
    hostsid = models.CommaSeparatedIntegerField(verbose_name=_("Hosts id"),
                                                null=False, blank=False, max_length=10000)
    created_by = models.CharField(
        verbose_name=_("Created by"), max_length=255, null=True, blank=True)
    revoked_by = models.CharField(
        verbose_name=_("Revoked by"), max_length=255, null=True, blank=True)

    def __unicode__(self):
        return "%s" % self.description

    class Meta:
        permissions = (
            ("view_maintenance", "Can view maintenance"),
        )

    def save_host_maintenance(self,):
        save_host_ok = True
        total_hosts = 0

        try:

            hostsid_list = self.hostsid.split(',')
            hosts = Host.objects.filter(pk__in=hostsid_list)
            for host in hosts:
                hm = HostMaintenance()
                hm.host = host
                hm.maintenance = self
                hm.hostname = host.hostname
                hm.save()
                total_hosts += 1

        except Exception, e:
            error = e.args[1]
            LOG.warn("Error: {}".format(error))
            self.status = self.REJECTED
            save_host_ok = False

        else:
            self.affected_hosts = total_hosts
            self.status = self.WAITING

        finally:
            # post_save signal has to be disconnected in order to avoid
            # recursive signal call
            post_save.disconnect(maintenance_post_save, sender=Maintenance)

            self.save()

            # connecting signal again
            post_save.connect(maintenance_post_save, sender=Maintenance)

        return save_host_ok

    def revoke_maintenance(self, request):
        if self.is_waiting_to_run:
            control.revoke(self.celery_task_id,)

            self.status = self.REVOKED
            self.revoked_by = request.user.username
            self.save()

            HostMaintenance.objects.filter(maintenance=self,
                                           ).update(status=HostMaintenance.REVOKED)
            return True

        return False

    def is_waiting_to_run(self):
        if self.status == self.FINISHED:
            LOG.info("Maintenance: {} has already run!".format(self))
            return False
        elif self.status == self.REJECTED:
            LOG.info("Maintenance: {} has been rejected".format(self))
            return False

        inspect = control.inspect()
        scheduled_tasks = inspect.scheduled()
        try:
            hosts = scheduled_tasks.keys()
        except Exception, e:
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


class HostMaintenance(BaseModel):
    ERROR = 0
    SUCCESS = 1
    RUNNING = 2
    ROLLBACK = 3
    WAITING = 4
    ROLLBACK_ERROR = 5
    ROLLBACK_SUCCESS = 6
    REVOKED = 7
    UNAVAILABLEHOST = 8
    UNAVAILABLECSHOSTATTR = 9

    MAINTENANCE_STATUS = (
        (ERROR, 'Error'),
        (SUCCESS, 'Success'),
        (RUNNING, 'Running'),
        (ROLLBACK, 'Rollback'),
        (WAITING, 'Waiting'),
        (ROLLBACK_ERROR, 'Rollback error'),
        (ROLLBACK_SUCCESS, 'Rollback success'),
        (REVOKED, 'Revoked'),
        (UNAVAILABLEHOST, 'Unavailable host'),
        (UNAVAILABLECSHOSTATTR, 'Unavailable cloudstack host attr'),
    )

    started_at = models.DateTimeField(verbose_name=_("Started at"), null=True)
    finished_at = models.DateTimeField(
        verbose_name=_("Finished at"), null=True)
    main_log = models.TextField(verbose_name=_("Main Log"),
                                null=True, blank=True)
    rollback_log = models.TextField(verbose_name=_("Rollback Log"),
                                    null=True, blank=True)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)
    host = models.ForeignKey(Host, related_name="host_maintenance",
                             on_delete=models.SET_NULL, null=True)
    hostname = models.CharField(verbose_name=_("Hostname"), max_length=255,
                                default='')
    maintenance = models.ForeignKey(Maintenance, related_name="maintenance",)

    class Meta:
        unique_together = (("host", "maintenance"),)
        index_together = [["host", "maintenance"], ]
        permissions = (
            ("view_hostmaintenance", "Can view host maintenance"),
        )

    def __unicode__(self):
        return "%s %s" % (self.host, self.maintenance)


class MaintenanceParameters(BaseModel):
    parameter_name = models.CharField(verbose_name=_(" Parameter name"),
                                      null=False, blank=False, max_length=100,)
    function_name = models.CharField(verbose_name=_(" Function name"),
                                     null=False, blank=False, max_length=100, choices=(_get_registered_functions()))
    maintenance = models.ForeignKey(Maintenance,
                                    related_name="maintenance_params",)

    def __unicode__(self):
        return "{} - {}".format(self.parameter_name, self.function_name)

    class Meta:
        permissions = (
            ("view_maintenance_parameters", "Can view maintenance parameters"),
        )

simple_audit.register(Maintenance)
simple_audit.register(HostMaintenance)
simple_audit.register(MaintenanceParameters)


#########
# SIGNALS#
#########

@receiver(pre_delete, sender=Maintenance)
def maintenance_pre_delete(sender, **kwargs):
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
            if maintenance.scheduled_for > datetime.now():
                task = execute_scheduled_maintenance.apply_async(args=[maintenance.id],
                                                                 eta=maintenance.scheduled_for.replace(tzinfo=tz.tzlocal()).astimezone(tz.tzutc()))
            else:
                task = execute_scheduled_maintenance.apply_async(args=[maintenance.id],
                                                                 countdown=5)

            maintenance.celery_task_id = task.task_id
            maintenance.save()
