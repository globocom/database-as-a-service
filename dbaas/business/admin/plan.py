# encoding: utf-8
from django.contrib import admin
from django_services import admin as services_admin
from ..service.plan import PlanService
from ..models import PlanAttribute


class PlanAttributeInline(admin.TabularInline):
    model = PlanAttribute


class PlanAdmin(services_admin.DjangoServicesAdmin):
    service_class = PlanService
    search_fields = ["name"]
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    save_on_top = True
    inlines = [
        PlanAttributeInline,
    ]

