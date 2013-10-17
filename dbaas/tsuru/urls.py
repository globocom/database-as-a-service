from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('tsuru.views',
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/?$', "service_add", name="tsuru.service_add"),
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/status/?$', "status", name="tsuru.status"),
)