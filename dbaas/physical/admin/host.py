# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django_services import admin as services_admin
from physical.models import Volume
from ..service.host import HostService


class VolumeInline(admin.TabularInline):
    model = Volume
    max_num = 0
    template = 'admin/physical/shared/inline_form.html'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + (
                'identifier', 'total_size_kb', 'used_size_kb', 'is_active'
            )
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False


class HostAdmin(services_admin.DjangoServicesAdmin):
    service_class = HostService
    search_fields = ("hostname", "identifier", "address", "os_description")
    list_display = (
        "hostname", "address", "offering", "os_description", "monitor_url_html"
    )
    readonly_fields = ("offering", "identifier")
    save_on_top = True
    inlines = [VolumeInline]

    def monitor_url_html(self, host):
        return "<a href='{0}' target='_blank'>{0}</a>".format(host.monitor_url)
    monitor_url_html.allow_tags = True
    monitor_url_html.short_description = "Monitor url"
    monitor_url_html.admin_order_field = "monitor_url"
