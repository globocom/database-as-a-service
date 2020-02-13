from django.contrib import admin
from djcelery.admin import PeriodicTaskAdmin
from djcelery.models import PeriodicTask


class PeriodicTaskDbaas(PeriodicTaskAdmin):
    actions = ['action_enable_plans','action_disable_plans']

    def action_enable_plans(self, request, queryset):
        queryset.update(enabled=True)
    action_enable_plans.short_description = "Enable selected plans"

    def action_disable_plans(self, request, queryset):
        queryset.update(enabled=False)
    action_disable_plans.short_description = "Disable selected plans"

admin.site.unregister(PeriodicTask)
admin.site.register(PeriodicTask, PeriodicTaskDbaas)
