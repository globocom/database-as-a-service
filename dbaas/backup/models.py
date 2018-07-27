# -*- coding: utf-8 -*-

from django.db import models
import simple_audit
from django.utils.translation import ugettext_lazy as _
from util.models import BaseModel
from physical.models import Environment
from physical.models import EngineType
import logging

LOG = logging.getLogger(__name__)


class BackupGroup(BaseModel):

    def __unicode__(self):
        return "Backup from {}".format(self.created_at)


class BackupInfo(BaseModel):

    SNAPSHOPT = 1
    BACKUPLOG = 2

    TYPE_CHOICES = (
        (SNAPSHOPT, 'Snapshot'),
        (BACKUPLOG, 'Backup Log')
    )

    RUNNING = 1
    SUCCESS = 2
    ERROR = 3
    WARNING = 4
    STATUS_CHOICES = (
        (RUNNING, 'Running'),
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
        (WARNING, 'Warning'),
    )

    class Meta:
        abstract = True

    start_at = models.DateTimeField(
        verbose_name=_("Start time"), null=False, blank=False)
    end_at = models.DateTimeField(
        verbose_name=_("End time"), null=True, blank=True)
    purge_at = models.DateTimeField(
        verbose_name=_("Purge time"), null=True, blank=True)
    type = models.IntegerField(
        verbose_name=_("Type"), choices=TYPE_CHOICES, null=False, blank=False)
    status = models.IntegerField(
        verbose_name=_("Status"), choices=STATUS_CHOICES, null=False, blank=False)
    instance = models.ForeignKey('physical.Instance', related_name="backup_instance",
                                 unique=False, null=True, blank=True, on_delete=models.SET_NULL)
    database_name = models.CharField(
        verbose_name=_("Database name"), max_length=100, null=True, blank=True,
        db_index=True)
    size = models.BigIntegerField(
        verbose_name=_("Size"), null=True, blank=True)
    environment = models.ForeignKey(
        'physical.Environment', related_name="backup_environment", unique=False, null=True, blank=True, on_delete=models.SET_NULL)
    error = models.CharField(
        verbose_name=_("Error"), max_length=400, null=True, blank=True)
    is_automatic = models.BooleanField(
        default=True, help_text='Backup required by DBaaS routine'
    )
    group = models.ForeignKey(
        BackupGroup, related_name='backups', null=True, blank=True
    )

    def __unicode__(self):
        return u"%s from %s started at %s" % (self.type, self.database_name, self.start_at)

    @property
    def was_successful(self):
        return self.status == Snapshot.SUCCESS

    @property
    def has_warning(self):
        return self.status == Snapshot.WARNING

    @property
    def was_error(self):
        return self.status == Snapshot.ERROR


class Snapshot(BackupInfo):

    snapshopt_id = models.CharField(
        verbose_name=_("Snapshot ID"), max_length=100, null=True, blank=True)
    snapshot_name = models.CharField(
        verbose_name=_("Snapshot Name"), max_length=200, null=True, blank=True)
    export_path = models.CharField(
        verbose_name=_("Export Path"), max_length=200, null=True, blank=True)

    def __unicode__(self):
        return u"Snapshot from %s started at %s" % (self.database_name, self.start_at)
