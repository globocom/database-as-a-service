from django.conf.urls import patterns, url
from .views import ExtraDnsView


urlpatterns = patterns('',
                       url(r"^extradns/(?P<pk>\d*)$",
                           ExtraDnsView.as_view(),
                           name="extradns-detail"),)
