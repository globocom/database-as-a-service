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
from .host import HostAPI
from .snapshot import SnapshotAPI
from .database_history import DatabaseHistoryAPI
from .database_restore import DatabaseRestoreAPI


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
