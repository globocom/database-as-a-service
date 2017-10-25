# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import admin
import api.urls

from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.generic.base import RedirectView


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

if settings.DBAAS_OAUTH2_LOGIN_ENABLE:
    from backstage_oauth2.views import BackstageOAuthRedirect
    django_login_view = admin.site.login
    admin.site.login = BackstageOAuthRedirect.as_view(provider='backstage')
    from django.http import HttpResponseRedirect
    from django.core.urlresolvers import reverse
    from django.contrib.auth import logout as auth_logout, REDIRECT_FIELD_NAME

    def ldap_login(request, *args, **kw):
        if request.user.is_authenticated():
            return HttpResponseRedirect(
                reverse('admin:index')
            )

        extra_context = {
            REDIRECT_FIELD_NAME: reverse('ldap_validation'),
        }
        return django_login_view(request, extra_context=extra_context, **kw)

    def ldap_validation(request, *args, **kw):
        user = request.user

        if (user.is_superuser or
             'admin' in user.team_set.values_list('name', flat=True)):
            return HttpResponseRedirect(
                reverse('admin:index')
            )
        else:
            auth_logout(request)
            return django_login_view(
                request,
                extra_context={'ldap_permission_error': 1},
                **kw
            )

    urlpatterns += patterns(
        '',
        url(r'^accounts/login/ldap/$', ldap_login, name='ldap_login'),
        url(r'^accounts/login/ldap/callback/$', ldap_validation, name='ldap_validation'),
        url(r'^accounts/', include('backstage_oauth2.urls')),
        url(r'', include('glb_version.urls')),
    )


# django flatpages
urlpatterns += patterns(
    'django.contrib.flatpages.views', (r'^(?P<url>.*/)$', 'flatpage'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
