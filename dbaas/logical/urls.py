from django.conf.urls import patterns, url
from .views import refresh_status
from .views import CredentialView, CredentialSSLView


urlpatterns = patterns('',
                       url(r"^credential/(?P<pk>\d*)$",
                           CredentialView.as_view(),
                           name="credential-detail"),
                       url(r"^status/(?P<database_id>\d*)$",
                           refresh_status,
                           name="logical_database_refresh_status"),
                       url(r"^credentialssl/(?P<pk>\d*)$",
                           CredentialSSLView.as_view(),
                           name="credentialssl-detail"),
                       )
