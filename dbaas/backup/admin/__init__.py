# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from ..models import Snapshot, LogConfiguration
from .snapshot import SnapshotAdmin
from .log_configuration import LogConfigurationAdmin


admin.site.register(Snapshot, SnapshotAdmin)
admin.site.register(LogConfiguration, LogConfigurationAdmin)
