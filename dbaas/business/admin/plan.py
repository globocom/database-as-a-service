# encoding: utf-8
from django.contrib import admin
from django_services import admin as services_admin
from ..service.plan import PlanService
from ..models import PlanAttribute
from ..form.plan_admin import PlanAttributeInlineFormset


class PlanAttributeInline(admin.TabularInline):
    model = PlanAttribute
    formset = PlanAttributeInlineFormset


class PlanAdmin(services_admin.DjangoServicesAdmin):
    service_class = PlanService
    save_on_top = True
    search_fields = ["name"]
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    filter_horizontal = ('environment',)
    inlines = [
        PlanAttributeInline,
    ]

