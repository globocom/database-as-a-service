# -*- coding:utf-8 -*-
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls import patterns, url, include

from .environment import EnvironmentAPI
from .plan import PlanAPI
from .engine import EngineAPI
from .engine_type import EngineTypeAPI
from .project import ProjectAPI
from .database import DatabaseAPI
from .credential import CredentialAPI
from .extra_dns import ExtraDnsAPI
from .task import TaskAPI
from .team import TeamAPI
from .user import UserAPI
from .host import HostAPI, CheckIsSlaveAPIView
from .snapshot import SnapshotAPI
from .database_history import DatabaseHistoryAPI
from .database_restore import DatabaseRestoreAPI
from .database_create import DatabaseCreateAPI
from .host_migrate import HostMigrateAPI
from .database_change_parameter import DatabaseChangeParameterAPI
from .add_readonly import AddInstancesToDatabaseAPI
from .database_resize import DatabaseResizeAPI
from database_reinstall_vm import DatabaseReinstallVMAPI
from .recreate_slave import RecreateSlaveAPI
from .database_upgrade import DatabaseUpgradeAPI
from .database_upgrade_patch import DatabaseUpgradePatchAPI
from .database_clone import DatabaseCloneAPI
from .database_destroy import DatabaseDestroyAPI
from .update_ssl import UpdateSslAPI
from .restart_database import RestartDatabaseAPI
from .databaase_migrate_engine import DatabaseMigrateEngineAPI
from .remove_readonly import RemoveInstanceDatabaseAPI


router = DefaultRouter()
urlpatterns = []

# physical
router.register(r'environment', EnvironmentAPI)
router.register(r'plan', PlanAPI)
router.register(r'engine', EngineAPI)
router.register(r'engine_type', EngineTypeAPI)
router.register(r'host', HostAPI)

# logical
router.register(r'project', ProjectAPI)
router.register(r'database', DatabaseAPI)
router.register(r'credential', CredentialAPI)
router.register(r'extra_dns', ExtraDnsAPI)
router.register(r'task', TaskAPI, base_name="task")
router.register(r'database_history', DatabaseHistoryAPI)
router.register(r'database_restore', DatabaseRestoreAPI)
router.register(r'database_create', DatabaseCreateAPI)
router.register(r'host_migrate', HostMigrateAPI)
router.register(r'database_change_parameter', DatabaseChangeParameterAPI)
router.register(r'add_instances_to_database', AddInstancesToDatabaseAPI)
router.register(r'remove_instance_database', RemoveInstanceDatabaseAPI)
router.register(r'database_resize', DatabaseResizeAPI)
router.register(r'database_reinstall_vm', DatabaseReinstallVMAPI)
router.register(r'recreate_slave', RecreateSlaveAPI)
router.register(r'database_upgrade', DatabaseUpgradeAPI)
router.register(r'database_upgrade_patch', DatabaseUpgradePatchAPI)
router.register(r'database_clone', DatabaseCloneAPI)
router.register(r'database_destroy', DatabaseDestroyAPI)
router.register(r'update_ssl', UpdateSslAPI)
router.register(r'restart_database', RestartDatabaseAPI)
router.register(r'database_migrate_engine', DatabaseMigrateEngineAPI)

if settings.CLOUD_STACK_ENABLED:
    from .integration_type import CredentialTypeAPI
    router.register(r'integration_type', CredentialTypeAPI)

    from .integration_credential import IntegrationCredentialAPI
    router.register(r'integration_credential',
                    IntegrationCredentialAPI, base_name="integration_credential")

    from dbaas_cloudstack.api import urls as cloudstack_api_urls
    urlpatterns += patterns('', url(r'^', include(cloudstack_api_urls)))

# account
router.register(r'team', TeamAPI)
router.register(r'user', UserAPI)
router.register(r'snapshot', SnapshotAPI)
urlpatterns += router.urls

# is_slave url
urlpatterns += [
    url(
        r'^host/(?P<hostname>[-\w.]+)/is_slave/$',
        CheckIsSlaveAPIView.as_view(),
        name='is_slave'
    )
]
