# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django_services import admin as services_admin
from ..service.plan import PlanService
from ..models import PlanAttribute
from ..forms import PlanAttributeInlineFormset


class PlanAttributeInline(admin.TabularInline):
    model = PlanAttribute
    formset = PlanAttributeInlineFormset


class PlanAdmin(services_admin.DjangoServicesAdmin):
    service_class = PlanService
    save_on_top = True
    search_fields = ["name"]
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    inlines = [
        PlanAttributeInline,
    ]

