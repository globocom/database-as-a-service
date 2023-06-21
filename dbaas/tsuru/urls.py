# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from views import (ListPlans, GetServiceStatus, GetServiceInfo, ServiceAdd,
                   ServiceAppBind, ServiceUnitBind, ServiceRemove,
                   ServiceJobBind)

urlpatterns = patterns(
    'tsuru.views',
    url(r'^resources/plans$', ListPlans.as_view(), name='list-plans'),
    url(r'^resources/(?P<database_name>\w+)/status$',
        GetServiceStatus.as_view(), name='service-status'),
    url(r'^services/(?P<database_name>\w+)$',
        GetServiceInfo.as_view(), name='service-info'),
    url(r'^resources$', ServiceAdd.as_view(), name='service-add'),
    url(r'^resources/(?P<database_name>\w+)$',
        ServiceRemove.as_view()),
    url(r'^resources/(?P<database_name>\w+)/bind$',
        ServiceUnitBind.as_view()),
    url(r'^resources/(?P<database_name>\w+)/bind-app$',
        ServiceAppBind.as_view(), name='service-app-bind'),
    url(r'^resources/(?P<database_name>\w+)/bind-job$',
        ServiceJobBind.as_view(), name='service-job-bind'),
    )
