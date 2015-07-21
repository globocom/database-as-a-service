# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin as services_admin
from django.contrib import admin
from ..service.host import HostService
from dbaas_cloudstack.models import HostAttr
from dbaas_nfsaas.models import HostAttr as HostAttrNfsaas


class HostAttrInline(admin.StackedInline):
    model = HostAttr
    max_num = 0
    template = 'admin/physical/shared/inline_form.html'

    def has_delete_permission(self, request, obj=None):
        return False


class HostAttrNfsaasInline(admin.StackedInline):
    model = HostAttrNfsaas
    max_num = 0
    template = 'admin/physical/shared/inline_form.html'

    def has_delete_permission(self, request, obj=None):
        return False


class HostAdmin(services_admin.DjangoServicesAdmin):
    service_class = HostService
    search_fields = ("hostname",)
    list_display = ("hostname", "address", "monitor_url_html",)
    save_on_top = True

    def monitor_url_html(self, host):
        return "<a href='%(u)s' target='_blank'>%(u)s</a>" % {'u': host.monitor_url}
    monitor_url_html.allow_tags = True
    monitor_url_html.short_description = "Monitor url"
    monitor_url_html.admin_order_field = "monitor_url"

    inlines = [
        HostAttrInline,
        HostAttrNfsaasInline,
    ]
