# -*- coding:utf-8 -*-
#from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter

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

urlpatterns = router.urls

# urlpatterns = patterns(
#     '',
#     # url(r'^$', 'api_help', name='api.index'),
#     # url(r'^', include(router.urls)),
#     # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
#     url('^logical', )
# )
