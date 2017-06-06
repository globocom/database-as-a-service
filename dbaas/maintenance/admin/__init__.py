# -*- coding:utf-8 -*-
from django.contrib import admin
from .. import models
from .maintenance import MaintenanceAdmin
from .host_maintenance import HostMaintenanceAdmin
from .database_upgrade import DatabaseUpgradeAdmin
from .database_resize import DatabaseResizeAdmin
from .database_change_parameter import DatabaseChangeParameterAdmin

admin.site.register(models.Maintenance, MaintenanceAdmin)
admin.site.register(models.HostMaintenance, HostMaintenanceAdmin)
admin.site.register(models.DatabaseUpgrade, DatabaseUpgradeAdmin)
admin.site.register(models.DatabaseResize, DatabaseResizeAdmin)
admin.site.register(models.DatabaseChangeParameter, DatabaseChangeParameterAdmin)
