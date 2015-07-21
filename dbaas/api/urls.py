# -*- coding:utf-8 -*-
#from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter
from django.http import HttpResponseRedirect
from django.conf.urls import patterns, url


# class MyRouter(DefaultRouter):
#
#     def get_api_root_view(self):
# return lambda r:
# HttpResponseRedirect('https://github.com/globocom/database-as-a-service/wiki/Introduction-to-the-API')

router = DefaultRouter()

# physical

from .environment import EnvironmentAPI
router.register(r'environment', EnvironmentAPI)

from .plan import PlanAPI
router.register(r'plan', PlanAPI)

from .engine import EngineAPI
router.register(r'engine', EngineAPI)

from .engine_type import EngineTypeAPI
router.register(r'engine_type', EngineTypeAPI)

# logical
from .project import ProjectAPI
router.register(r'project', ProjectAPI)

from .database import DatabaseAPI
router.register(r'database', DatabaseAPI)

from .credential import CredentialAPI
router.register(r'credential', CredentialAPI)

from .extra_dns import ExtraDnsAPI
router.register(r'extra_dns', ExtraDnsAPI)

from .task import TaskAPI
router.register(r'task', TaskAPI, base_name="task")

from django.conf import settings
if settings.CLOUD_STACK_ENABLED:
    from .integration_type import CredentialTypeAPI
    router.register(r'integration_type', CredentialTypeAPI)

    from .integration_credential import IntegrationCredentialAPI
    router.register(r'integration_credential',
                    IntegrationCredentialAPI, base_name="integration_credential")

# account
from .team import TeamAPI
router.register(r'team', TeamAPI)

from .user import UserAPI
router.register(r'user', UserAPI)


urlpatterns = router.urls

#from .task import TaskDetail
#urlpatterns += patterns( url('^task/(?P<task_id>.+)/$', TaskDetail.as_view()), )

# urlpatterns = patterns(
#     '',
#     # url(r'^$', 'api_help', name='api.index'),
#     # url(r'^', include(router.urls)),
#     # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
#     url('^logical', )
# )
