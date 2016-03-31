# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.host_maintenance import HostMaintenanceService
from ..forms import HostMaintenanceForm
from .. import models
from django.contrib import admin
import logging
from django.utils.html import format_html

LOG = logging.getLogger(__name__)


class HostMaintenanceAdmin(admin.ModelAdmin):
    actions = None
    service_class = HostMaintenanceService
    search_fields = ("maintenance__description", "hostname", "status")
    list_display = (
        "maintenance", "hostname", "started_at", "finished_at", "friendly_status")
    fields = ("maintenance", "hostname", "status", "started_at",
              "finished_at", "main_log", "rollback_log")
    readonly_fields = fields
    form = HostMaintenanceForm

    ordering = ["-started_at"]

    def friendly_status(self, host_maintenance):

        html_success = '<span class="label label-info">Success</span>'
        html_rejected = '<span class="label label-important">{}</span>'
        html_waiting = '<span class="label label-warning">Waiting</span>'
        html_running = '<span class="label label-success">Running</span>'
        html_revoked = '<span class="label label-primary">{}</span>'

        if host_maintenance.status == models.HostMaintenance.SUCCESS:
            return format_html(html_success)
        elif host_maintenance.status == models.HostMaintenance.ERROR:
            return format_html(html_rejected.format("Error"))
        elif host_maintenance.status == models.HostMaintenance.ROLLBACK:
            return format_html(html_rejected.format("Rollback"))
        elif host_maintenance.status == models.HostMaintenance.ROLLBACK_ERROR:
            return format_html(html_rejected.format("Rollback Error"))
        elif host_maintenance.status == models.HostMaintenance.ROLLBACK_SUCCESS:
            return format_html(html_rejected.format("Rollback Succes"))
        elif host_maintenance.status == models.HostMaintenance.WAITING:
            return format_html(html_waiting)
        elif host_maintenance.status == models.HostMaintenance.RUNNING:
            return format_html(html_running)
        elif host_maintenance.status == models.HostMaintenance.REVOKED:
            return format_html(html_revoked.format("Revoked"))
        elif host_maintenance.status == models.HostMaintenance.UNAVAILABLEHOST:
            return format_html(html_revoked.format("Unavailable Host"))
        elif host_maintenance.status == models.HostMaintenance.UNAVAILABLECSHOSTATTR:
            return format_html(html_revoked.format("Unavailable CsHost"))

    friendly_status.short_description = "Status"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
