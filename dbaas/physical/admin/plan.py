# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django_services import admin as services_admin
from ..service.plan import PlanService
from ..models import PlanAttribute
from integrations.iaas.cloudstack.models import PlanAttr
from integrations.storage.nfsaas.models import PlanAttr as PlanAttrNfsaas
from .. import forms


class PlanAttributeInline(admin.TabularInline):
    model = PlanAttribute
    formset = forms.PlanAttributeInlineFormset


class PlanAttrInline(admin.StackedInline):
    model = PlanAttr
    max_num = 1
    template = 'admin/physical/shared/inline_form.html'
    def has_delete_permission(self, request, obj=None):
        return False

class PlanAttrNfsaasInline(admin.StackedInline):
    model = PlanAttrNfsaas
    max_num = 1
    template = 'admin/physical/shared/inline_form.html'
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
    inlines = [
        PlanAttributeInline,
        PlanAttrInline,
        PlanAttrNfsaasInline,
    ]

