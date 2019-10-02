from django.conf.urls import patterns, url
from .views import refresh_status
from .views import (CredentialView, CredentialSSLView,
                    credential_parameter_by_name)


urlpatterns = patterns(
    '',
    url(r"^credential/(?P<pk>\d*)$",
        CredentialView.as_view(),
        name="credential-detail"),
    url(r"^status/(?P<database_id>\d*)$",
        refresh_status,
        name="logical_database_refresh_status"),
    url(r"^credentialssl/(?P<pk>\d*)$",
        CredentialSSLView.as_view(),
        name="credentialssl-detail"),
    url(r"^(?P<env_id>\d+)/credential_parameter_by_name/(?P<param_name>[\w\-\_]+)$",
        credential_parameter_by_name,
        name="credential_parameter_by_name"),
)
