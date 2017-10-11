# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from ..forms.replication_topology import ReplicationTopologyForm
from ..models import TopologyParameterCustomValue


class ParamCustomValueInline(admin.TabularInline):
    model = TopologyParameterCustomValue


class ReplicationTopologyAdmin(admin.ModelAdmin):
    form = ReplicationTopologyForm
    list_filter = ("has_horizontal_scalability", "engine")
    search_fields = ("name",)
    list_display = ("name", "versions", "has_horizontal_scalability")

    filter_horizontal = ("parameter",)

    save_on_top = True
    inlines = [ParamCustomValueInline]

    change_form_template = "admin/physical/replicationtopology/change_form.html"
    add_form_template = "admin/change_form.html"

    def versions(self, obj):
        return ", ".join([str(engine.version) for engine in obj.engine.all()])
