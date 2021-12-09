# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from ..models import Engine
from ..models import EngineType
from ..models import ReplicationTopology
from ..models import Script


class ReplicationTopologyFilter(admin.SimpleListFilter):
    title = 'replication_topology'
    parameter_name = 'script_id'

    def lookups(self, request, model_admin):
        rps = [(r.id, r.name) for r in ReplicationTopology.objects.all()]
        return tuple(rps)

    def queryset(self, request, queryset):
        if self.value():
            return Script.objects.filter(id=ReplicationTopology.objects.get(id=self.value()).script.id)
        else:
            return queryset


class EngineFilter(admin.SimpleListFilter):
    title = 'engine'
    parameter_name = 'engine'

    def lookups(self, request, model_admin):
        engines = [(e.id, e.name+'_'+e.version) for e in Engine.objects.all()]
        return tuple(engines)

    def queryset(self, request, queryset):
        if self.value():
            return Script.objects.filter(id__in=list(ReplicationTopology.objects.filter(engine=self.value()).
                                                     values_list('script__id', flat=True)))
        else:
            return queryset


class EngineTypeFilter(admin.SimpleListFilter):
    title = 'engine_type'
    parameter_name = 'engine_type'

    def lookups(self, request, model_admin):
        ets = [(et.id, et.name) for et in EngineType.objects.all()]
        return tuple(ets)

    def queryset(self, request, queryset):
        if self.value():
            return Script.objects.filter(id__in=list(ReplicationTopology.objects.filter(engine__in=Engine.objects.filter(
                engine_type=self.value())).values_list('script__id', flat=True)))
        else:
            return queryset


class ScriptAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_filter = (ReplicationTopologyFilter, EngineFilter, EngineTypeFilter)
