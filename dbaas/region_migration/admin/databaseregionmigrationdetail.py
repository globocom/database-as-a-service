# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.databaseregionmigrationdetail import DatabaseRegionMigrationDetailService
from .. import models
import logging
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

LOG = logging.getLogger(__name__)


class DatabaseRegionMigrationDetailAdmin(admin.DjangoServicesAdmin):
    actions = None
    service_class = DatabaseRegionMigrationDetailService
    search_fields = ("step", "status",)
    list_display = ("database_region_migration", "step", "scheduled_for",
                    "friendly_status", "friendly_direction", "started_at",
                    "finished_at", "created_by", "revoked_by",)
    fields = ("database_region_migration", "step", "scheduled_for",
              "status", "started_at", "finished_at", "created_by",
              "revoked_by", "log", "celery_task_id")
    readonly_fields = fields

    ordering = ["-scheduled_for", ]

    def get_readonly_fields(self, request, obj=None):
        detail = obj
        self.max_num = None
        if detail and detail.status == models.DatabaseRegionMigrationDetail.WAITING:
            self.change_form_template = "admin/region_migration/databaseregionmigrationdetail/custom_change_form.html"
        else:
            self.change_form_template = None

        return self.fields

        return ()

    def revoke_detail(request, id):
        import celery
        from system.models import Configuration
        celery_inpsect = celery.current_app.control.inspect()

        celery_workers = Configuration.get_by_name_as_list('celery_workers',)

        try:
            workers = celery_inpsect.ping().keys()
        except Exception, e:
            LOG.warn("All celery workers are down! {} :(".format(e))
            messages.add_message(request, messages.ERROR,
                                 "Migration can't be revoked because all celery workers are down!",)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if workers and workers != celery_workers:
            LOG.warn("At least one celery worker is down! :(")
            messages.add_message(request, messages.ERROR,
                "Migration can't be revoked because at least one celery worker is down!",)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        detail = models.DatabaseRegionMigrationDetail.objects.get(id=id)
        if detail.status == detail.WAITING:
            if detail.revoke_maintenance(request):
                messages.add_message(request, messages.SUCCESS,
                                     "Migration revoked!",)
            else:
                messages.add_message(request, messages.ERROR,
                                     "Migration has already started!",)
        else:
            messages.add_message(request, messages.ERROR,
                                 "Migration can't be revoked!",)

        return HttpResponseRedirect(reverse('admin:region_migration_databaseregionmigrationdetail_changelist'))

    buttons = [
        {'url': 'revoke_detail',
         'textname': 'Revoke Migration',
         'func': revoke_detail,
         'confirm': u'Do you really want to revoke this migration?',
         'id': 'revoke_migration'},
    ]

    def change_view(self, request, object_id, form_url='', extra_context={}):
        extra_context['buttons'] = self.buttons
        return super(DatabaseRegionMigrationDetailAdmin, self).change_view(request,
                                                                           object_id,
                                                                           form_url,
                                                                           extra_context=extra_context)

    def get_urls(self):
        from django.conf.urls import url
        urls = super(DatabaseRegionMigrationDetailAdmin, self).get_urls()
        my_urls = list((url(r'^(.+)/%(url)s/$' % b, self.admin_site.admin_view(b['func'])) for b in self.buttons))
        return my_urls + urls

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
        elif detail.status == models.DatabaseRegionMigrationDetail.RUNNING:
            return format_html(html_running)
        elif detail.status == models.DatabaseRegionMigrationDetail.REVOKED:
            return format_html(html_revoked.format("Revoked"))
        elif detail.status == models.DatabaseRegionMigrationDetail.ERROR:
            return format_html(html_rejected.format("Error"))

    friendly_status.short_description = "Status"

    def friendly_direction(self, detail):
        message = "Backward"

        if detail.is_migration_up:
            message = "Foward"

        return message


    friendly_direction.short_description = "Direction"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
