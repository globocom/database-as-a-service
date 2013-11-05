from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('account.views',
    url(r'^profile/(?P<user_id>\d+)/?$', "profile", name="account.profile"),
)