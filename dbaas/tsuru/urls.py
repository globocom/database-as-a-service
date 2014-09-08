from django.conf.urls.defaults import *
from django.conf import settings
from views2 import ListPlans, GetServiceStatus, GetServiceInfo, ServiceAdd

urlpatterns = patterns('tsuru.views',
    url(r'^resources/plans$', ListPlans.as_view()),
    url(r'^resources/(?P<database_id>\d+)/status$', GetServiceStatus.as_view()),
    url(r'^services/(?P<database_id>\d+)$', GetServiceInfo.as_view()),
    url(r'^resources$', ServiceAdd.as_view()),
)
