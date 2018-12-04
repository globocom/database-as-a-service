# -*- coding:utf-8 -*-
from django.contrib import admin
from .. import models
from .maintenance import MaintenanceAdmin
from .host_maintenance import HostMaintenanceAdmin
from .database_upgrade import DatabaseUpgradeAdmin
from .database_resize import DatabaseResizeAdmin
from .database_change_parameter import DatabaseChangeParameterAdmin
from .database_create import DatabaseCreateAdmin
from .database_destroy import DatabaseDestroyAdmin
from .database_restore import DatabaseRestoreAdmin
from .database_reinstall_vm import DatabaseReinstallVMAdmin
from .database_configure_ssl import DatabaseConfigureSSLAdmin
from .host_migrate import HostMigrateAdmin
from .database_migrate import DatabaseMigrateAdmin


admin.site.register(models.Maintenance, MaintenanceAdmin)
admin.site.register(models.HostMaintenance, HostMaintenanceAdmin)
admin.site.register(models.DatabaseUpgrade, DatabaseUpgradeAdmin)
admin.site.register(models.DatabaseResize, DatabaseResizeAdmin)
admin.site.register(models.DatabaseChangeParameter, DatabaseChangeParameterAdmin)
admin.site.register(models.DatabaseCreate, DatabaseCreateAdmin)
admin.site.register(models.DatabaseDestroy, DatabaseDestroyAdmin)
admin.site.register(models.DatabaseRestore, DatabaseRestoreAdmin)
admin.site.register(models.DatabaseReinstallVM, DatabaseReinstallVMAdmin)
admin.site.register(models.DatabaseConfigureSSL, DatabaseConfigureSSLAdmin)
admin.site.register(models.HostMigrate, HostMigrateAdmin)
admin.site.register(models.DatabaseMigrate, DatabaseMigrateAdmin)
