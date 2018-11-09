# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from views import (ListPlans, GetServiceStatus, GetServiceInfo, ServiceAdd,
                   ServiceAppBind, ServiceUnitBind, ServiceRemove)

urlpatterns = patterns('tsuru.views',
                       url(r'^resources/plans$', ListPlans.as_view()),
                       url(r'^resources/(?P<database_name>\w+)/status$',
                           GetServiceStatus.as_view()),
                       url(r'^services/(?P<database_name>\w+)$',
                           GetServiceInfo.as_view()),
                       url(r'^resources$', ServiceAdd.as_view()),
                       url(r'^resources/(?P<database_name>\w+)$',
                           ServiceRemove.as_view()),
                       url(r'^resources/(?P<database_name>\w+)/bind$',
                           ServiceUnitBind.as_view()),
                       url(r'^resources/(?P<database_name>\w+)/bind-app$',
                           ServiceAppBind.as_view()),
                       )
