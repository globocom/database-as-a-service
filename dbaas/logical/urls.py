from django.conf.urls import patterns, url
from .views import CredentialView
from .views import get_status



urlpatterns = patterns('',
                       url(r"^credential/(?P<pk>\d*)$",
                           CredentialView.as_view(),
                           name="credential-detail"),
                       url(r"^status/(?P<database_id>\d*)$",
                           get_status,
                           name="logical_database_refresh_status"),
                       )
