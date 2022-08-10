from django.conf.urls import url

from views import SubUsedResourceReport, DatabaseReport

urlpatterns = [
    url(r'^analyzing/reports/$', SubUsedResourceReport.as_view(),
        name='sub_used_resource_report'),
    url(r'^analyzing/report/$', DatabaseReport.as_view(),
        name='database_report'),
]
