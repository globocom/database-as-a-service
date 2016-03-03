# -*- coding: utf-8 -*-

from django.db import models
import simple_audit
from django.utils.translation import ugettext_lazy as _
from util.models import BaseModel
from physical.models import Environment
from physical.models import EngineType
import logging

LOG = logging.getLogger(__name__)


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
    STATUS_CHOICES = (
        (RUNNING, 'Running'),
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
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

    def __unicode__(self):
        return u"%s from %s started at %s" % (self.type, self.database_name, self.start_at)


class Snapshot(BackupInfo):

    snapshopt_id = models.CharField(
        verbose_name=_("Snapshot ID"), max_length=100, null=True, blank=True)
    snapshot_name = models.CharField(
        verbose_name=_("Snapshot Name"), max_length=200, null=True, blank=True)
    export_path = models.CharField(
        verbose_name=_("Export Path"), max_length=200, null=True, blank=True)

    def __unicode__(self):
        return u"Snapshot from %s started at %s" % (self.database_name, self.start_at)


class LogConfiguration(BaseModel):

    environment = models.ForeignKey(Environment, null=False, blank=False, on_delete=models.CASCADE)
    engine_type = models.ForeignKey(EngineType, null=False, blank=False, on_delete=models.CASCADE)

    retention_days = models.SmallIntegerField(verbose_name=_("Backup Retention Days"),
                                              max_length=2, null=False, blank=False, default=7)
    filer_path = models.CharField(
        verbose_name=_("Filer Path"), max_length=200, null=False, blank=False)
    mount_point_path = models.CharField(
        verbose_name=_("Mount Point Path"), max_length=200, null=False, blank=False)
    log_path = models.CharField(
        verbose_name=_("Database Log Path"), max_length=200, null=False, blank=False)
    backup_log_script = models.CharField(
        verbose_name=_("Backup Log Script"), max_length=200, null=False, blank=False)
    config_backup_log_script = models.CharField(
        verbose_name=_("Config Backup Log Script"), max_length=200, null=False, blank=False)
    clean_backup_log_script = models.CharField(
        verbose_name=_("Clean Backup Log Script"), max_length=200, null=False, blank=False)
    cron_minute = models.CharField(
        verbose_name=_("Crontab minute"), max_length=10, null=False, blank=False)
    cron_hour = models.CharField(
        verbose_name=_("Crontab hour"), max_length=10, null=False, blank=False)

    class Meta:
        unique_together = (
            ('environment', 'engine_type')
        )

    def __unicode__(self):
        return u"Backup config for %s environment and %s engine type" % (self.environment, self.engine_type)


simple_audit.register(LogConfiguration)
