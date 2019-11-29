# -*- coding: utf-8 -*-
from datetime import datetime
from django.db import models
from util.models import BaseModel
from physical.models import Instance, Environment, Volume


class BackupGroup(BaseModel):

    def __unicode__(self):
        return "Backup from {}".format(self.created_at)


class BackupInfo(BaseModel):

    SNAPSHOPT = 1
    TYPE_CHOICES = (
        (SNAPSHOPT, 'Snapshot'),
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

    start_at = models.DateTimeField(null=False, blank=False)
    end_at = models.DateTimeField(null=True, blank=True)
    purge_at = models.DateTimeField(null=True, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES, null=False, blank=False)
    status = models.IntegerField(
        choices=STATUS_CHOICES, null=False, blank=False
    )
    instance = models.ForeignKey(
        Instance, related_name="backup_instance",
        unique=False, null=True, blank=True, on_delete=models.SET_NULL
    )
    database_name = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )
    size = models.BigIntegerField(null=True, blank=True)
    environment = models.ForeignKey(
        Environment, related_name="backup_environment",
        unique=False, null=True, blank=True, on_delete=models.SET_NULL
    )
    error = models.CharField(max_length=400, null=True, blank=True)
    is_automatic = models.BooleanField(
        default=True, help_text='Backup required by DBaaS routine'
    )
    group = models.ForeignKey(
        BackupGroup, related_name='backups', null=True, blank=True
    )
    volume = models.ForeignKey(
        Volume, related_name="backups",
        unique=False, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __unicode__(self):
        return "{} from {} started at {}".format(
            self.type, self.database_name, self.start_at
        )

    @property
    def was_successful(self):
        return self.status == Snapshot.SUCCESS

    @property
    def has_warning(self):
        return self.status == Snapshot.WARNING

    @property
    def was_error(self):
        return self.status == Snapshot.ERROR

    def set_error(self, msg):
        self.status = Snapshot.ERROR
        self.error = msg
        self.size = 0
        self.end_at = datetime.now()
        self.purge_at = datetime.now()
        self.save()

    @classmethod
    def create(cls, instance, group, volume):
        snapshot = cls()
        snapshot.start_at = datetime.now()
        snapshot.type = Snapshot.SNAPSHOPT
        snapshot.status = Snapshot.RUNNING
        snapshot.instance = instance
        snapshot.environment = instance.databaseinfra.environment
        snapshot.group = group
        snapshot.database_name = instance.databaseinfra.databases.first().name
        snapshot.volume = volume
        snapshot.save()
        return snapshot


class Snapshot(BackupInfo):
    snapshopt_id = models.CharField(
        verbose_name="Snapshot ID", max_length=100, null=True, blank=True
    )
    snapshot_name = models.CharField(
        verbose_name="Snapshot Name", max_length=200, null=True, blank=True
    )
    volume_path = models.CharField(
        verbose_name="Volume Path", max_length=255, null=True, blank=True
    )

    def __unicode__(self):
        return "Snapshot from {} started at {}".format(
            self.database_name, self.start_at
        )

    def done(self, response):
        self.snapshopt_id = response['identifier']
        self.snapshot_name = response['description']
