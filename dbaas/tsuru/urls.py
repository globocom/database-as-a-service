from django.conf.urls.defaults import *
from django.conf import settings
from views2 import ListPlans, GetServiceStatus

urlpatterns = patterns('tsuru.views',
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/(?P<service_name>.[^/]+)/hostname/(?P<host>.+)/?$', "service_unbind", name="tsuru.service_unbind"),
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/(?P<service_name>.[^/]+)/status/?$', "service_status", name="tsuru.service_status"),
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/(?P<service_name>.[^/]+)/?$', "service_bind_remove", name="tsuru.service_bind_remove"),
    url(r'^(?P<engine_name>\w+)/(?P<engine_version>.+)/resources/?$', "service_add", name="tsuru.service_add"),
    url(r'^resources/plans$', ListPlans.as_view()),
    url(r'^resources/(?P<database_id>\d+)/status$', GetServiceStatus.as_view()),
)
