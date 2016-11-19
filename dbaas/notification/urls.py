from django.conf.urls import patterns, url
import views


urlpatterns = patterns(
    views,
    url(r"^tasks_running/$", views.running_tasks_api, name="notification:tasks_running"),
)
