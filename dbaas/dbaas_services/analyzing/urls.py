from django.conf.urls import url

from views import SubUsedResourceReport

urlpatterns = [
    url(r'^analyzing/reports/$', SubUsedResourceReport.as_view(),
        name='sub_used_resource_report'),
]
