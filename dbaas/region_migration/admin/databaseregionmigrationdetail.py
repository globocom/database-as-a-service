# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.databaseregionmigrationdetail import DatabaseRegionMigrationDetailService
from .. import models
import logging
from django.utils.html import format_html

LOG = logging.getLogger(__name__)


class DatabaseRegionMigrationDetailAdmin(admin.DjangoServicesAdmin):
    actions = None
    service_class = DatabaseRegionMigrationDetailService
    search_fields = ("step", "status")
    list_display = ("database_region_migration", "step", "scheduled_for",
                    "friendly_status", "started_at", "finished_at", "created_by",
                    "revoked_by",)
    fields = ("database_region_migration", "step", "scheduled_for",
              "status", "started_at", "finished_at", "created_by",
              "revoked_by", "log",)
    readonly_fields = fields

    ordering = ["-scheduled_for", ]

    def friendly_status(self, detail):

        html_success = '<span class="label label-info">Success</span>'
        html_rejected = '<span class="label label-important">{}</span>'
        html_waiting = '<span class="label label-warning">Waiting</span>'
        html_running = '<span class="label label-success">Running</span>'
        html_revoked = '<span class="label label-primary">{}</span>'

        if detail.status == models.DatabaseRegionMigrationDetail.SUCCESS:
            return format_html(html_success)
        elif detail.status == models.DatabaseRegionMigrationDetail.ROLLBACK:
            return format_html(html_rejected.format("Rollback"))
        elif detail.status == models.DatabaseRegionMigrationDetail.WAITING:
            return format_html(html_waiting)
        elif detail.status == models.HostMaintenance.RUNNING:
            return format_html(html_running)
        elif detail.status == models.HostMaintenance.REVOKED:
            return format_html(html_revoked.format("Revoked"))

    friendly_status.short_description = "Status"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
