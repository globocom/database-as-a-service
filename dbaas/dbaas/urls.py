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
    url(r'^([^/]+)/tsuru/', include('tsuru.urls', namespace='tsuru')),
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
    from backstage_oauth2.views import (BackstageOAuthRedirect,
                                        BackstageOAuthCallback)
    django_login_view = admin.site.login
    admin.site.login = BackstageOAuthRedirect.as_view(provider='backstage')
    from django.http import HttpResponseRedirect
    from django.core.urlresolvers import reverse
    from django.contrib.auth import logout as auth_logout
    from django.views.generic import View

    class DBaaSBackstageOAuthCallback(BackstageOAuthCallback):
        @staticmethod
        def get_user(user_cls, username, email):
            return user_cls.objects.get(email=email)

        @staticmethod
        def transform_user_metadata(user_metadata, info, username, email):
            from allaccess.compat import get_user_model
            User = get_user_model()
            user_metadata.update({
                User.USERNAME_FIELD: email,
            })
            return user_metadata

    class LDAPLogin(View):

        @staticmethod
        def can_login(user):
            if user.is_staff and user.is_active:
                return True
            return False 

        def get(self, *args, **kw):
            user = self.request.user
            if user.is_authenticated():
                if self.can_login(user):
                    return HttpResponseRedirect(
                        reverse('admin:index')
                    )
                else:
                    auth_logout(self.request)
                    return django_login_view(
                        self.request,
                        extra_context={
                            'ldap_permission_error': 1,
                            'ldap_error_msg': ('Only superusers or DBA Role '
                                               'users can login with LDAP')
                        },
                        **kw
                    )

            return django_login_view(self.request, **kw)

        def post(self, *args, **kw):
            return django_login_view(self.request, **kw)

    urlpatterns += patterns(
        '',
        url(r'^accounts/login/ldap/$', LDAPLogin.as_view(), name='ldap_login'),
        url(r'^accounts/callback/(?P<provider>backstage)/$',
            DBaaSBackstageOAuthCallback.as_view(), name='allaccess-callback'),
        url(r'^accounts/', include('backstage_oauth2.urls')),
        url(r'', include('glb_version.urls')),
    )

if settings.LOGOUT_REDIRECT_URL:
    logout_pattern = patterns(
        '',
        url(
            r'^admin/logout/$',
            'django.contrib.auth.views.logout',
            {'next_page': settings.LOGOUT_REDIRECT_URL},
            name='logout'
        ),
    )
    urlpatterns = logout_pattern + urlpatterns


# django flatpages
urlpatterns += patterns(
    'django.contrib.flatpages.views', (r'^(?P<url>.*/)$', 'flatpage'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
