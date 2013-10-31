# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django_services import admin
from ..service.database import DatabaseService
from ..forms import DatabaseForm
from ..models import Database

MB_FACTOR = 1.0 / 1024.0 / 1024.0

LOG = logging.getLogger(__name__)

class DatabaseAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseService
    search_fields = ("name", "databaseinfra__name")
    list_display = ("name", "get_capacity_html", "endpoint", "is_in_quarantine")
    list_filter = ("databaseinfra", "project", "is_in_quarantine")
    add_form_template = "logical/database_add_form.html"
    change_form_template = "logical/database_change_form.html"
    delete_button_name = "Delete"
    fieldsets_add = (
        (None, {
            'fields': ('name', 'project', 'plan')
            }
        ),
    )
    fieldsets_change = (
        (None, {
            'fields': ('name', 'project', 'group')
            }
        ),
    )

    def get_capacity_html(self, database):
        if database.capacity > .75:
            bar_type = "danger"
        elif database.capacity > .5:
            bar_type = "warning"
        else:
            bar_type = "success"
        return """
<div class="progress progress-%(bar_type)s">
    <p style="position: absolute; padding-left: 10px;">%(used)d MB of %(total)d MB</p>
    <div class="bar" style="width: %(p)d%%;"></div>
</div>""" % {
            "p": int(database.capacity*100),
            "used": database.used_size * MB_FACTOR,
            "total": database.total_size * MB_FACTOR,
            "bar_type": bar_type,
        }
    get_capacity_html.allow_tags = True
    get_capacity_html.short_description = "Capacity"

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = []
        if not obj:
            # adding new database
            return DatabaseForm
        # Tradicional form
        return super(DatabaseAdmin, self).get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets_change if obj else self.fieldsets_add

    def get_readonly_fields(self, request, obj=None):
        """
        if in edit mode, name is readonly.
        """
        if obj: #In edit mode
            return ('name', 'group', 'databaseinfra') + self.readonly_fields
        return self.readonly_fields

    # def add_view(self, request, form_url='', extra_context=None, **kwargs):
    #     return super(DatabaseAdmin, self).add_view(request, form_url, extra_context, **kwargs)


    def change_view(self, request, object_id, form_url='', extra_context=None):
        database = Database.objects.get(id=object_id)
        extra_context = extra_context or {}
        if database.is_in_quarantine:
            extra_context['delete_button_name'] = self.delete_button_name
        else:
            extra_context['delete_button_name'] = "Move to quarantine"
        return super(DatabaseAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)


