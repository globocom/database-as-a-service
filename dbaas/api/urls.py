# -*- coding:utf-8 -*-
#from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter
from .project import ProjectAPI

router = DefaultRouter()
router.register(r'project', ProjectAPI)

urlpatterns = router.urls

# urlpatterns = patterns(
#     '',
#     # url(r'^$', 'api_help', name='api.index'),
#     # url(r'^', include(router.urls)),
#     # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
#     url('^logical', )
# )
