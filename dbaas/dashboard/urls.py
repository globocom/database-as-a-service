from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('dashboard.views',
    url(r"^$", "dashboard", name="dashboard.index"),
)