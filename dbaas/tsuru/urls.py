from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('tsuru.views',
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/(?P<service_name>.+)/status/?$', "status", name="tsuru.status"),
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/(?P<service_name>.+)/hostname/(?P<host>.+)/?$', "service_unbind", name="tsuru.service_unbind"),
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/(?P<service_name>.+)/?$', "service_bind", name="tsuru.service_bind"),
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/?$', "service_add", name="tsuru.service_add"),
)