# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db import models
from django.utils.translation import ugettext_lazy as _
from logical.models import Database
from util.models import BaseModel
from region_migration.migration_steps import get_engine_steps


LOG = logging.getLogger(__name__)

class DatabaseRegionMigration(BaseModel):
    database =  models.ForeignKey(Database, null= False, unique= True)
    current_step = models.PositiveSmallIntegerField(verbose_name=_("Current Step"), null=False,
        blank= False, default=0)
    next_step = models.PositiveSmallIntegerField(verbose_name=_("Next Step"), null=True,
        blank= False)

    def __unicode__(self):
        return '{} on step {}'.format(self.database, self.current_step)

    def get_steps(self,):
        return get_engine_steps(self.database.engine)

    def get_current_step(self,):
        return get_engine_steps(self.database.engine)[self.step]



class DatabaseRegionMigrationDetail(BaseModel):
    WAITING = 0
    RUNNING = 1
    SUCCESS = 2
    ROLLBACK = 3
    REVOKED = 4

    MAINTENANCE_STATUS = (
        (SUCCESS, 'Success'),
        (RUNNING, 'Running'),
        (WAITING, 'Waiting'),
        (ROLLBACK, 'Rollback'),
        (REVOKED, 'Revoked')
    )
    database_region_migration = models.ForeignKey(DatabaseRegionMigration,
        related_name="details", null=False)
    step = models.PositiveSmallIntegerField(verbose_name=_("Step"), null=False,
        blank= False)
    scheduled_for = models.DateTimeField(verbose_name=_("Schedule for"), null=False)
    started_at = models.DateTimeField(verbose_name=_("Started at"), null=True, blank=True)
    finished_at = models.DateTimeField(verbose_name=_("Finished at"),null=True, blank=True)
    created_by = models.CharField(verbose_name=_("Created by"), max_length=255, null=False,
        blank=False)
    revoked_by = models.CharField(verbose_name=_("Revoked by"), max_length=255, null=True,
        blank=True)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)
    log = models.TextField(verbose_name=_("Log"),null=False, blank=False)


    class Meta:
        unique_together = (
            ('database_region_migration', 'step', 'scheduled_for',)
        )


    def __unicode__(self):
        return " Detail for %s" % (self.database_region_migration)


simple_audit.register(DatabaseRegionMigration, DatabaseRegionMigrationDetail)
