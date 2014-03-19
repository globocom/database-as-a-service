# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django_services import admin as services_admin
from ..service.plan import PlanService
from ..models import PlanAttribute
from .. import forms
from providers.models import PlanCSAttribute
from django.conf import settings


class PlanAttributeInline(admin.TabularInline):
    model = PlanAttribute
    formset = forms.PlanAttributeInlineFormset

class PlanCSAttributeInline(admin.StackedInline):
    model = PlanCSAttribute
    max_num = 1
    #verbose_name = ""
    def has_delete_permission(self, request, obj=None):
        return False
    
class PlanAdmin(services_admin.DjangoServicesAdmin):
    form = forms.PlanForm
    service_class = PlanService
    save_on_top = True
    search_fields = ["name"]
    list_filter = ("is_active", )
    list_display = ("name", "is_active", "is_default")
    filter_horizontal = ("environments",)
    if settings.CLOUD_STACK_ENABLED:
        inlines = [
            PlanAttributeInline,
            PlanCSAttributeInline, 
        ]
    else:
        inlines = [
            PlanAttributeInline,
        ]

