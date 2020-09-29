# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.html import format_html
from .database_maintenance_task import DatabaseMaintenanceTaskAdmin


class DatabaseSetSSLNotRequiredAdmin(DatabaseMaintenanceTaskAdmin):

    def maintenance_action(self, maintenance_task):
        if (not maintenance_task.is_status_error or
                not maintenance_task.can_do_retry):
            return 'N/A'

        url = maintenance_task.database.get_set_ssl_not_required_retry_url()
        html = ("<a title='Retry' class='btn btn-info' "
                "href='{}'>Retry</a>").format(url)
        return format_html(html)
