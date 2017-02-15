# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.generic.base import RedirectView
import admin
import api.urls

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url='/admin'), name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^dashboard/', include('dashboard.urls')),
    url(r'^([^/]+)/tsuru/', include('tsuru.urls')),
    url(r'^logical/', include('logical.urls')),
    url(r'^account/', include('account.urls')),
    url(r'^system/', include('system.urls')),
    url('^api/', include(api.urls)),
    url('^extra_dns/', include('extra_dns.urls')),
    url(r'^admin/', include('dbaas_services.analyzing.urls')),
    url(r'^notification/', include('notification.urls'), name="notification"),
    url(r'^ckeditor/', include('ckeditor.urls')),
    url(r'^physical/', include('physical.urls')),
)

# django flatpages
urlpatterns += patterns(
    'django.contrib.flatpages.views', (r'^(?P<url>.*/)$', 'flatpage'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
