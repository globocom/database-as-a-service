# -*- coding:utf-8 -*-
from django.contrib import admin
from .. import models
from .maintenance import MaintenanceAdmin

admin.site.register(models.Maintenance, MaintenanceAdmin)
