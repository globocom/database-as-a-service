from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('graphite_metrics.views',
    url(r"^$", "graphite_metrics", name="graphite_metrics.index"),
)
