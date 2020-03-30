# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.utils.html import format_html

from django.contrib import admin


class TaskScheduleAdmin(admin.ModelAdmin):
    list_display = ("method_path", "link_database", "status", "scheduled_for",
                    "finished_at")
    search_fields = ('method_path', 'database__name')

    list_filter = (
        "status",
    )

    ordering = ('scheduled_for',)

    def link_database(self, task_schedule):
        url = reverse('admin:logical_database_maintenance',
                      args=(task_schedule.database.id,))
        link_database = """<a href="{}"> {} </a> """.format(
            url, task_schedule.database.name
        )
        return format_html(link_database)

    link_database.short_description = "Database"
