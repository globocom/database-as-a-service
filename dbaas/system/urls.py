from django.conf.urls import patterns, url
from .views import CeleryHealthCheckView


urlpatterns = patterns('',
                       url(r"^celery/healthcheck.html",
                           CeleryHealthCheckView, name="celery-healthcheck"),
                       )
