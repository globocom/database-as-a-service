# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.generic.base import RedirectView
import admin
import api.urls

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
    url(r'^account/', include('account.urls')),
    url('^api/', include(api.urls)),    
    (r'^ckeditor/', include('ckeditor.urls')),
)

# django flatpages
urlpatterns += patterns('django.contrib.flatpages.views',
    (r'^(?P<url>.*/)$', 'flatpage'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
