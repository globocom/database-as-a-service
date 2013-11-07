from django.conf.urls.defaults import patterns, url
from .views import CredentialView


urlpatterns = patterns('',
    
    url(r"^credential/(?P<pk>\d*)$", CredentialView.as_view(), name="credential-detail"),
)
