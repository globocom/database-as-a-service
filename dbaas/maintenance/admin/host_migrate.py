# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from maintenance.models import HostMigrate
from notification.tasks import TaskRegister
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class HostMigrateAdmin(DatabaseMaintenanceTaskAdmin):

    list_filter = [
        "status", "zone", "environment", "host"
    ]
    search_fields = ("task__id", "task__task_id", "host")

    list_display = (
        "host", "zone", "environment", "current_step", "friendly_status",
        "maintenance_action", "link_task", "link_database_migrate",
        "started_at", "finished_at"
    )
    readonly_fields = (
        "host", "zone", "environment", "link_task", "link_database_migrate",
        "started_at", "finished_at", "status", "task_schedule",
        "maintenance_action", "database_migrate"
    )
    ordering = ["-started_at"]

    def link_database_migrate(self, maintenance_task):
        database_migrate = maintenance_task.database_migrate
        if not database_migrate:
            return 'N/A'
        url = reverse(
            'admin:maintenance_databasemigrate_change',
            args=(database_migrate.id,)
        )
        return format_html(
            "<a href={}>{}/{}/Stage:{}</a>".format(
                url, database_migrate.database.name,
                database_migrate.environment,
                database_migrate.migration_stage
            )
        )
    link_database_migrate.short_description = "Database Migrate"

  