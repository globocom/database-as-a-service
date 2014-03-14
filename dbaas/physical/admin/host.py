# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.host import HostService


class HostAdmin(admin.DjangoServicesAdmin):
    service_class = HostService
    search_fields = ("hostname",)
    list_display = ("hostname","cp_id", "monitor_url_html",)
    save_on_top = True
    
    def monitor_url_html(self, host):
        return "<a href='%(u)s' target='_blank'>%(u)s</a>" % {'u': host.monitor_url }
    monitor_url_html.allow_tags = True
    monitor_url_html.short_description = "Monitor url"
    monitor_url_html.admin_order_field = "monitor_url"
