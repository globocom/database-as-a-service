# -*- coding: utf-8 -*-
from django_services import admin
from django.utils.html import format_html
from django.core.urlresolvers import reverse
from django.conf.urls import url, patterns
from django.http import HttpResponseRedirect
from datetime import datetime
from notification.models import TaskHistory
from ..models import DatabaseRegionMigration
from ..models import DatabaseRegionMigrationDetail
from ..service.databaseregionmigration import DatabaseRegionMigrationService
from ..tasks import execute_database_region_migration


class DatabaseRegionMigrationAdmin(admin.DjangoServicesAdmin):
    model = DatabaseRegionMigration
    list_display = ('database', 'current_step_description', 'next_step_description', 'warning', 'schedule_next_step_html')
    actions = None
    service_class = DatabaseRegionMigrationService
    list_display_links = ()

    def __init__(self, *args, **kwargs):
        super(DatabaseRegionMigrationAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def schedule_next_step_html(self, databaseregionmigration):
        html = []

        if databaseregionmigration.next_step and databaseregionmigration.next_step < len(databaseregionmigration.get_steps()) - 1:
            html.append("<a class='btn btn-info' href='%s/schedulenextstep'><i class='icon-calendar icon-white'></i></a>" % (databaseregionmigration.id))

        return format_html("".join(html))

    schedule_next_step_html.short_description = "Schedule next step"

    def get_urls(self):
        urls = super(DatabaseRegionMigrationAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^/?(?P<databaseregionmigration_id>\d+)/schedulenextstep/$',
                self.admin_site.admin_view(self.databaseregionmigration_view)),
        )
        return my_urls + urls

    def databaseregionmigration_view(self, request, databaseregionmigration_id):
        database_region_migration = DatabaseRegionMigration.objects.get(id=databaseregionmigration_id)
        database_region_migration_detail = DatabaseRegionMigrationDetail(
            database_region_migration=database_region_migration, step=database_region_migration.next_step,
            scheduled_for=datetime.now(),
            created_by=request.user.username)
        database_region_migration_detail.save()
        database_region_migration.next_step = None
        database_region_migration.save()

        task_history = TaskHistory()
        task_history.task_name = "execute_database_region_migration"
        task_history.task_status = task_history.STATUS_WAITING

        task_history.arguments = "Database name: {}, Step: {}".format(database_region_migration.database.name,
            database_region_migration_detail.database_region_migration.next_step_description())
        task_history.user = request.user
        task_history.save()
        execute_database_region_migration.apply_async(args=[database_region_migration_detail.id, task_history, request.user], countdown=1)

        url = reverse('admin:notification_taskhistory_changelist')
        return HttpResponseRedirect(url + "?user=%s" % request.user.username) 
