from django.conf.urls.defaults import patterns, url
from .views import CeleryHealthCheckView


urlpatterns = patterns('',    
    url(r"^celery/healthcheck.html", CeleryHealthCheckView, name="celery-healthcheck"),
)
