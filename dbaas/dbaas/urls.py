# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.generic.base import RedirectView
import admin
import django_services.api.urls

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
    url(r'^tsuru/', include('tsuru.urls')),
    url(r'^logical/', include('logical.urls')),
    url('^api/', include(django_services.api.urls))

)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
