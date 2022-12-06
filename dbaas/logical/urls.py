from django.conf.urls import patterns, url
from .views import refresh_status, toggle_monitoring, set_attention
from .views import (CredentialView, CredentialSSLView,
                    credential_parameter_by_name, check_offering_sizes)


urlpatterns = patterns(
    '',
    url(r"^credential/(?P<pk>\d*)$",
        CredentialView.as_view(),
        name="credential-detail"),
    url(r"^status/(?P<database_id>\d*)$",
        refresh_status,
        name="logical_database_refresh_status"),
    url(r"^toggle_monitoring/(?P<database_id>\d*)$",
        toggle_monitoring,
        name="toggle_monitoring"),
    url(r"^set_attention/(?P<database_id>\d*)$",
        set_attention,
        name="attention_with_gcp_settings_divergence"),
    url(r"^credentialssl/(?P<pk>\d*)$",
        CredentialSSLView.as_view(),
        name="credentialssl-detail"),
    url(r"^(?P<env_id>\d+)/credential_parameter_by_name/(?P<param_name>[\w\-\_]+)$",
        credential_parameter_by_name,
        name="credential_parameter_by_name"),
    url(r"^check_offering_sizes/",
        check_offering_sizes,
        name="check_offering_sizes"),
)
