# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.database import DatabaseService
from ..forms import DatabaseForm


class DatabaseAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseService
    search_fields = ("name", "databaseinfra__name")
    list_display = ("name", "endpoint", "get_capacity_html")
    list_filter = ("databaseinfra", "project",)
    change_form_template = "logical/database_change_form.html"
    fieldsets = (
        (None, {
            'fields': ('name', 'project', 'plan')
            }
        ),
    )
    form = DatabaseForm

    def get_capacity_html(self, database):
        if database.capacity > .75:
            bar_type = "danger"
        elif database.capacity > .5:
            bar_type = "warning"
        else:
            bar_type = "success"
        return """
<div class="progress progress-striped active">
    <div class="bar bar-%(bar_type)s" style="width: %(p)d%%;">%(used)d of %(total)d MB used</div>
</div>""" % {
            "p": int(database.capacity*100),
            "used": database.used_size,
            "total": database.total_size,
            "bar_type": bar_type,
        }
    get_capacity_html.allow_tags = True
    get_capacity_html.short_description = "Capacity"

    def get_readonly_fields(self, request, obj=None):
        """
        if in edit mode, name is readonly.
        """
        if obj: #In edit mode
            return ('name',) + self.readonly_fields

        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None, **kwargs):
        return super(DatabaseAdmin, self).add_view(request, form_url, extra_context, **kwargs)


    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(DatabaseAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)


