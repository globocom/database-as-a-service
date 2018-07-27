# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin as services_admin
from ..service.host import HostService


class HostAdmin(services_admin.DjangoServicesAdmin):
    service_class = HostService
    search_fields = (
        "hostname", "nfsaas_host_attributes__nfsaas_path",
        "address", "os_description"
    )
    list_display = (
        "hostname", "address", "offering", "os_description", "monitor_url_html"
    )
    readonly_fields = ("offering", "identifier")
    save_on_top = True

    def monitor_url_html(self, host):
        return "<a href='{0}' target='_blank'>{0}</a>".format(host.monitor_url)
    monitor_url_html.allow_tags = True
    monitor_url_html.short_description = "Monitor url"
    monitor_url_html.admin_order_field = "monitor_url"
