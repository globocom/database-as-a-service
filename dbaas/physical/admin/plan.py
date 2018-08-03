# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django_services import admin as services_admin
from ..service.plan import PlanService
from ..models import PlanAttribute, Engine
from dbaas_dnsapi.models import PlanAttr as PlanAttrDNSAPI
from .. import forms
from physical import models


class PlanAttributeInline(admin.TabularInline):
    model = PlanAttribute


class PlanAttrDNSAPIInline(admin.StackedInline):
    model = PlanAttrDNSAPI
    max_num = 1
    template = 'admin/physical/shared/inline_form.html'

    def has_delete_permission(self, request, obj=None):
        return False


def action_activate_plans(modeladmin, request, queryset):
    queryset.update(is_active=True)
action_activate_plans.short_description = "Activate plans"


def action_deactivate_plans(modeladmin, request, queryset):
    queryset.update(is_active=False)
action_deactivate_plans.short_description = "Deactivate plans"


class PlanAdmin(services_admin.DjangoServicesAdmin):
    form = forms.PlanForm
    service_class = PlanService
    save_on_top = True
    search_fields = ["name"]
    list_filter = (
        "is_active", "engine", "environments", "is_ha", "has_persistence"
    )
    list_display = (
        "name", "engine", "environment", "is_active", "provider", "is_ha",
    )
    filter_horizontal = ("environments",)
    inlines = [
        PlanAttributeInline,
        PlanAttrDNSAPIInline,
    ]

    add_form_template = "admin/physical/plan/add_form.html"
    change_form_template = "admin/physical/plan/change_form.html"
    actions = [action_activate_plans, action_deactivate_plans]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = self.add_extra_context(extra_context)

        return super(PlanAdmin, self).change_view(
            request=request, object_id=object_id, form_url=form_url,
            extra_context=extra_context
        )

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = self.add_extra_context(extra_context)
        return super(PlanAdmin, self).add_view(
            request=request, form_url=form_url, extra_context=extra_context
        )

    def add_extra_context(self, context):
        if not context:
            context = {}

        context['replication_topologies_engines'] = self._get_replication_topologies_engines()
        context['engines'] = self._get_engines_type()

        return context

    def _get_replication_topologies_engines(self):
        engines = {}
        for topology in models.ReplicationTopology.objects.all():
            for engine in topology.engine.all():
                current_engine = str(engine)
                if current_engine not in engines:
                    engines[current_engine] = []
                engines[current_engine].append(topology)

        return engines

    def _get_engines_type(self):
        return {
            engine: engine.engine_type.is_in_memory
            for engine in Engine.objects.all()
        }
