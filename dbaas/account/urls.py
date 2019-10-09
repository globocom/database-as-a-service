from django.conf.urls import patterns, url
from forms.change_password_form import ChangePasswordForm
from dbaas import settings

urlpatterns = patterns(
    'account.views',
    url(r'^profile/(?P<user_id>\d+)/?$', "profile", name="account.profile"),
    url(r"^team_contacts/(?P<team_id>\d*)$", "team_contacts", name="contacts"),
)

if settings.LDAP_ENABLED:
    urlpatterns += patterns(
        '',
        url(r'^password_reset/done/',
            'django.contrib.auth.views.password_reset_done', {
                'template_name': 'ldap/password_reset_done.html'
            }, 'account_password_reset_done'),

        url(r'^password_reset/', 'django.contrib.auth.views.password_reset', {
            'template_name': 'ldap/password_reset.html',
            'post_reset_redirect': '/account/password_reset/done/',
            'email_template_name': 'ldap/password_reset_email.html'
        }, 'account_password_reset'),
        url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/',
            'django.contrib.auth.views.password_reset_confirm', {
                'template_name': 'ldap/password_reset_confirm.html',
                'post_reset_redirect': '/account/reset/done/',
                'set_password_form': ChangePasswordForm
            }, 'account_reset'),
        url(r'^reset/done/',
            'django.contrib.auth.views.password_reset_complete', {
                'template_name': 'ldap/password_reset_complete.html'
            }, 'account_reset_done'),
    )
