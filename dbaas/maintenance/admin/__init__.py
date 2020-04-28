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
from .database_upgrade_patch import DatabaseUpgradePatchAdmin
from .recreate_slave import RecreateSlaveAdmin
from .update_ssl import UpdateSslAdmin
from .migrate_engine import DatabaseMigrateEngineAdmin
from .database_clone import DatabaseCloneAdmin
from .add_instances_to_database import AddInstancesToDatabaseAdmin
from .task_schedule import TaskScheduleAdmin
from .restart_database import RestartDatabaseAdmin


admin.site.register(models.Maintenance, MaintenanceAdmin)
admin.site.register(models.HostMaintenance, HostMaintenanceAdmin)
admin.site.register(models.DatabaseUpgrade, DatabaseUpgradeAdmin)
admin.site.register(models.DatabaseResize, DatabaseResizeAdmin)
admin.site.register(
    models.DatabaseChangeParameter, DatabaseChangeParameterAdmin
)
admin.site.register(models.DatabaseCreate, DatabaseCreateAdmin)
admin.site.register(models.DatabaseDestroy, DatabaseDestroyAdmin)
admin.site.register(models.DatabaseRestore, DatabaseRestoreAdmin)
admin.site.register(models.DatabaseReinstallVM, DatabaseReinstallVMAdmin)
admin.site.register(models.DatabaseConfigureSSL, DatabaseConfigureSSLAdmin)
admin.site.register(models.HostMigrate, HostMigrateAdmin)
admin.site.register(models.DatabaseMigrate, DatabaseMigrateAdmin)
admin.site.register(models.DatabaseUpgradePatch, DatabaseUpgradePatchAdmin)
admin.site.register(models.DatabaseMigrateEngine, DatabaseMigrateEngineAdmin)
admin.site.register(models.RecreateSlave, RecreateSlaveAdmin)
admin.site.register(models.UpdateSsl, UpdateSslAdmin)
admin.site.register(models.DatabaseClone, DatabaseCloneAdmin)
admin.site.register(models.AddInstancesToDatabase, AddInstancesToDatabaseAdmin)
admin.site.register(models.TaskSchedule, TaskScheduleAdmin)
admin.site.register(models.RestartDatabase, RestartDatabaseAdmin)
