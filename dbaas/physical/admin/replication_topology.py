# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from ..forms.replication_topology import ReplicationTopologyForm


class ReplicationTopologyAdmin(admin.ModelAdmin):
    form = ReplicationTopologyForm
    list_filter = ("has_horizontal_scalability", "engine")
    search_fields = ("name",)
    list_display = ("name", "versions", "has_horizontal_scalability")
    save_on_top = True

    def versions(self, obj):
        return ", ".join([str(engine.version) for engine in obj.engine.all()])
