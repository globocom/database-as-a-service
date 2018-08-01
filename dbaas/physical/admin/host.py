# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.safestring import mark_safe
from django.contrib import admin
from django_services import admin as services_admin
from workflow.steps.util.volume_provider import VolumeProviderBase
from physical.models import Volume
from ..service.host import HostService


class VolumeInline(admin.TabularInline):
    model = Volume
    max_num = 0
    template = 'admin/physical/shared/inline_form.html'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + (
                'identifier', 'total_size_kb', 'used_size_kb', 'is_active',
                'path'
            )
        return self.readonly_fields

    def path(self, obj):
        if not obj.identifier:
            return
        provider = VolumeProviderBase(obj.host.instances.first())
        return mark_safe(provider.get_path(obj))

    def has_delete_permission(self, request, obj=None):
        return False


class HostAdmin(services_admin.DjangoServicesAdmin):
    service_class = HostService
    search_fields = (
        "hostname", "identifier", "address", "os_description",
        "volumes__identifier"
    )
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
