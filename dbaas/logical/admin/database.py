# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django_services import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from ..service.database import DatabaseService
from ..forms import DatabaseForm
from ..models import Database
from account.models import UserRepository
from util.html import render_progress_bar

MB_FACTOR = 1.0 / 1024.0 / 1024.0

LOG = logging.getLogger(__name__)

class DatabaseAdmin(admin.DjangoServicesAdmin):
    perm_manage_quarantine_database = "logical.can_manage_quarantine_databases"
    service_class = DatabaseService
    search_fields = ("name", "databaseinfra__name")
    list_display = ["name", "get_capacity_html", "endpoint", "quarantine_dt_format"]
    list_filter = ("databaseinfra", "project", "is_in_quarantine")
    add_form_template = "logical/database_add_form.html"
    change_form_template = "logical/database_change_form.html"
    delete_button_name = "Delete"
    fieldsets_add = (
        (None, {
            'fields': ('name', 'project', 'environment', 'plan',)
            }
        ),
    )
    
    fieldsets_change_basic = (
        (None, {
            'fields': ['name', 'project', 'group',]
            }
        ),
    )
    
    fieldsets_change_advanced = (
        (None, {
            'fields': fieldsets_change_basic[0][1]['fields'] + ["is_in_quarantine"]
            }
        ),
    )

    def quarantine_dt_format(self, database):
        return database.quarantine_dt or ""
    quarantine_dt_format.short_description = "Quarantine since"
    quarantine_dt_format.admin_order_field = 'quarantine_dt'

    def get_capacity_html(self, database):
        try:
            message = "%d MB of %d MB" % (database.used_size * MB_FACTOR, database.total_size * MB_FACTOR)
            return render_progress_bar(database.capacity*100, message=message)
        except:
            # any error show Unkown message and log error. This avoid break page if there is a problem
            # with some database
            LOG.error('Error getting capacity of database %s', database)
            return "Unkown"
    get_capacity_html.short_description = "Capacity"

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = []
        if not obj:
            # adding new database
            return DatabaseForm
        # Tradicional form
        return super(DatabaseAdmin, self).get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            groups = UserRepository.get_groups_for(user=request.user)
            LOG.info("user %s groups: %s" % (request.user, groups))
            if groups:
                obj.group = groups[0]
                LOG.info("Team accountable for database %s set to %s" % (obj, obj.group))

        obj.save()

    def get_fieldsets(self, request, obj=None):
        if obj: #In edit mode
            if request.user.has_perm(self.perm_manage_quarantine_database):
                self.fieldsets_change = self.fieldsets_change_advanced
            else:
                self.fieldsets_change = self.fieldsets_change_basic

        return self.fieldsets_change if obj else self.fieldsets_add

    def get_readonly_fields(self, request, obj=None):
        """
        if in edit mode, name is readonly.
        """
        if obj: #In edit mode
            return ('name', 'group', 'databaseinfra') + self.readonly_fields
        return self.readonly_fields


    def queryset(self, request):
        qs = super(DatabaseAdmin, self).queryset(request)
        if request.user.has_perm(self.perm_manage_quarantine_database):
            return qs

        return qs.filter(is_in_quarantine=False, group__in=[group.id for group in request.user.groups.all()])

    def has_add_permission(self, request):
        """User must be set to at least one group to be able to add database"""
        groups = UserRepository.get_groups_for(user=request.user)
        if not groups:
            return False
        else:
            return super(DatabaseAdmin, self).has_add_permission(request)

    def add_view(self, request, form_url='', extra_context=None):
        groups = UserRepository.get_groups_for(user=request.user)
        LOG.info("user %s groups: %s" % (request.user, groups))
        if not groups:
            self.message_user(request, _("You must be set to at least one team or group."), level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:logical_database_changelist'))
        return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)


    def change_view(self, request, object_id, form_url='', extra_context=None):
        database = Database.objects.get(id=object_id)
        extra_context = extra_context or {}
        if database.is_in_quarantine:
            extra_context['delete_button_name'] = self.delete_button_name
        else:
            extra_context['delete_button_name'] = "Delete"
        return super(DatabaseAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

