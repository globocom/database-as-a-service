# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.generic.base import RedirectView
from rest_framework import routers
from .resources import ResourcesViewSet
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from adminplus.sites import AdminSitePlus
import django_services.api.urls

admin.site = AdminSitePlus()
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', RedirectView.as_view(url='/admin'), name='home'),
    # url(r'^dbaas/', include('dbaas.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^dashboard/', include('dashboard.urls')),
    url('^api/', include(django_services.api.urls))

)

router = routers.DefaultRouter()
router.register(r'resources', ResourcesViewSet, base_name="resources")

urlpatterns += router.urls

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
