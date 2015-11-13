# -*- coding: utf-8 -*-
from django.db import models
from util.models import BaseModel
from django.utils.translation import ugettext_lazy as _


class AnalyzeRepository(BaseModel):
    analyzed_at = models.DateTimeField(verbose_name=_("Analyzed at"), db_index=True)
    database_name = models.CharField(verbose_name=_("Database name"), max_length=60,
                                     unique=False, null=False, blank=False,
                                     db_index=True)
    databaseinfra_name = models.CharField(verbose_name=_("Database Infra name"), max_length=60,
                                          unique=False, null=False, blank=False,
                                          db_index=True)
    instance_name = models.CharField(verbose_name=_("Instance name"), max_length=100,
                                     unique=False, null=False, blank=False,
                                     db_index=True)
    engine_name = models.CharField(verbose_name=_("Engine name"), max_length=20,
                                   unique=False, null=False, blank=False,
                                   db_index=True)
    environment_name = models.CharField(verbose_name=_("Environment name"), max_length=30,
                                        unique=False, null=False, blank=False,
                                        db_index=True)
    cpu_alarm = models.BooleanField(verbose_name=_("CPU alarm"), default=False)
    cpu_threshold = models.IntegerField(verbose_name=_("CPU Threshold"), unique=False,
                                        null=False, default=50)
    memory_alarm = models.BooleanField(verbose_name=_("Memory alarm"), default=False)
    memory_threshold = models.IntegerField(verbose_name=_("Memory Threshold"), unique=False,
                                           null=False, default=50)
    volume_alarm = models.BooleanField(verbose_name=_("Volume alarm"), default=False)
    volume_threshold = models.IntegerField(verbose_name=_("Volume Threshold"), unique=False,
                                           null=False, default=50)
    email_sent = models.BooleanField(verbose_name=_("Email sent?"), default=False,
                                     db_index=True)

    class Meta:
        unique_together = (
            ('analyzed_at', 'instance_name',)
        )
        permissions = (
            ("view_analyzerepository", "Can view analyze repository"),
        )
        verbose_name = 'Resource use report'

    def __unicode__(self):
        return self.instance_name


class ExecutionPlan(BaseModel):
    plan_name = models.CharField(verbose_name=_("Execution plan name"), max_length=60,
                                 unique=True, null=False, blank=False,
                                 db_index=True)
    metrics = models.CharField(verbose_name=_("Metrics used by plan"), max_length=200,
                               unique=True, null=False, blank=False, db_index=True,
                               help_text=_('Comma separated list of metrics. Ex.: cpu.cpu_used,cpu.cpu_free,...'))
    threshold = models.IntegerField(verbose_name=_("Threshold"), unique=False,
                                    null=False, default=50)
    proccess_function = models.CharField(verbose_name=_("Proccess function used by service"),
                                         max_length=150, unique=False, null=False, blank=False,)
    adapter = models.CharField(verbose_name=_("Adapter used by service"),
                               max_length=150, unique=False, null=False, blank=False,)
    alarm_repository_attr = models.CharField(verbose_name=_("Alarm field on repository"),
                                             max_length=150, unique=True, null=False,
                                             blank=False,)
    threshold_repository_attr = models.CharField(verbose_name=_("Threshold field on repository"),
                                                 max_length=150, unique=True, null=False,
                                                 blank=False,)
    minimum_value = models.IntegerField(verbose_name=_("Minimum resource"), unique=False,
                                        null=False, blank=False,)
    field_to_check_value = models.CharField(verbose_name=_("Field to check minimum value"),
                                            max_length=150, unique=True, null=False,
                                            blank=False, help_text=_('{model}.{field}'))

    class Meta:
        permissions = (
            ("view_executionplan", "Can view Execution Plan"),
        )

    def __parse_metrics(self):
        return self.metrics.split(',')

    def setup_execution_params(self):
        return {'metrics': self.__parse_metrics(), 'proccess_function': self.proccess_function,
                'threshold': self.threshold, 'adapter': self.adapter}

    def __unicode__(self):
        return self.plan_name
