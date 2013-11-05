from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('logical.views',
    url(r"credential/(?P<credential_id>\d+)/reset_password", "reset_password", name="reset_password"),
)
