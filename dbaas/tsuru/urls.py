from django.conf.urls.defaults import *
from django.conf import settings
from views import ListPlans, GetServiceStatus, GetServiceInfo, ServiceAdd, ServiceBind, ServiceRemove

urlpatterns = patterns('tsuru.views',
    url(r'^resources/plans$', ListPlans.as_view()),
    url(r'^resources/(?P<database_name>\w+)/status$', GetServiceStatus.as_view()),
    url(r'^services/(?P<database_name>\w+)$', GetServiceInfo.as_view()),
    url(r'^resources$', ServiceAdd.as_view()),
    url(r'^resources/(?P<database_name>\w+)$', ServiceRemove.as_view()),
    url(r'^resources/(?P<database_name>\w+)/bind$', ServiceBind.as_view()),
)
