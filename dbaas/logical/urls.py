from django.conf.urls import patterns, url
from .views import CredentialView, CredentialSSLView


urlpatterns = patterns('',
                       url(r"^credential/(?P<pk>\d*)$",
                           CredentialView.as_view(),
                           name="credential-detail"),
                       url(r"^credentialssl/(?P<pk>\d*)$",
                           CredentialSSLView.as_view(),
                           name="credentialssl-detail"),
                       )
