from django.contrib import admin
from djcelery.admin import PeriodicTaskAdmin
from djcelery.models import PeriodicTask


class PeriodicTaskDbaas(PeriodicTaskAdmin):
    actions = ['action_enable_tasks', 'action_disable_tasks']

    def _set_tasks_status(self, queryset, status):
        for periodic_task in queryset:
            periodic_task.enabled = status
            periodic_task.save()

    def action_enable_tasks(self, request, queryset):
        self._set_tasks_status(queryset, True)
    action_enable_tasks.short_description = "Enable selected tasks"

    def action_disable_tasks(self, request, queryset):
        self._set_tasks_status(queryset, False)
    action_disable_tasks.short_description = "Disable selected tasks"


admin.site.unregister(PeriodicTask)
admin.site.register(PeriodicTask, PeriodicTaskDbaas)
