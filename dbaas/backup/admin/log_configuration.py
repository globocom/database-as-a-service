# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
import logging


LOG = logging.getLogger(__name__)


class LogConfigurationAdmin(admin.ModelAdmin):

    list_filter = ("environment", "engine_type")

    list_display = ("environment", "engine_type", "retention_days",
                    "filer_path", "mount_point_path", "log_path",
                    "cron_minute", "cron_hour")
