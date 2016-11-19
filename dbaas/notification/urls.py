from django.conf.urls import patterns, url
import views


urlpatterns = patterns(
    views,
    url(r"^tasks_running/$", views.running_tasks_api, name="notification:tasks_running"),
    url(r"^tasks_waiting/$", views.waiting_tasks_api, name="notification:tasks_waiting"),
)
