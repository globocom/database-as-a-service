# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django_services import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.html import format_html, escape
from ..service.database import DatabaseService
from ..forms import DatabaseForm, DatabaseForm
from ..models import Database
from account.models import Team
from drivers import DatabaseAlreadyExists
from logical.templatetags import capacity
from system.models import Configuration

LOG = logging.getLogger(__name__)

class DatabaseAdmin(admin.DjangoServicesAdmin):
    """
    the form used by this view is returned by the method get_form
    """

    database_add_perm_message = _("You must be set to at least one team to add a database, and the service administrator has been notified about this.")
    perm_manage_quarantine_database = "logical.can_manage_quarantine_databases"
    perm_add_database_infra = "physical.add_databaseinfra"

    service_class = DatabaseService
    search_fields = ("name", "databaseinfra__name")
    list_display_basic = ["name_html", "engine_type", "environment", "plan", "status", "get_capacity_html", ]
    list_display_advanced = list_display_basic + ["quarantine_dt_format"]
    list_filter_basic = ["project", "databaseinfra__environment", "databaseinfra__engine", "databaseinfra__plan"]
    list_filter_advanced = list_filter_basic + ["databaseinfra", "is_in_quarantine", "team"]
    add_form_template = "logical/database/database_add_form.html"
    change_form_template = "logical/database/database_change_form.html"
    delete_button_name = "Delete"
    fieldsets_add = (
        (None, {
            'fields': ('name', 'description', 'project', 'engine', 'environment', 'team', 'plan', 'is_in_quarantine')
            }
        ),
    )
    
    fieldsets_change_basic = (
        (None, {
            'fields': ['name', 'description', 'project', 'team',]
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

    def environment(self, database):
        return database.environment

    environment.admin_order_field = 'name'

    def plan(self, database):
        return database.plan

    plan.admin_order_field = 'name'

    def status(self, database):

        html_ok = '<span class="label label-success">Alive</span>'
        html_nook = '<span class="label label-important">Dead</span>'

        database_status = database.database_status
        if database_status.is_alive:
            return format_html(html_ok)
        else:
            return format_html(html_nook)

    def description_html(self, database):

        html = []
        html.append("<ul>")
        html.append("<li>Engine Type: %s</li>" % database.engine_type)
        html.append("<li>Environment: %s</li>" % database.environment)
        html.append("<li>Plan: %s</li>" % database.plan)
        html.append("</ul>")

        return format_html("".join(html))

    description_html.short_description = "Description"

    def name_html(self, database):
        try:
            ed_point = escape(database.get_endpoint())
        except:
            ed_point = None
        html = '%(name)s <a href="javascript:void(0)" title="%(title)s" data-content="%(endpoint)s" class="show-endpoint"><span class="icon-info-sign"></span></a>' % {
            'name': database.name,
            'endpoint': ed_point,
            'title': _("Show Endpoint")
        }
        return format_html(html)
    name_html.short_description = _("name")
    name_html.admin_order_field = "name"

    def engine_type(self, database):
        return database.engine_type

    engine_type.admin_order_field = 'name'

    def get_capacity_html(self, database):
        try:
            return capacity.render_capacity_html(database)
        except:
            return None

    get_capacity_html.short_description = "Capacity"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        filter teams for the ones that the user is associated, unless the user has ther
        perm to add databaseinfra. In this case, he should see all teams.
        """
        if not request.user.has_perm(self.perm_add_database_infra):
            if db_field.name == "team":
                kwargs["queryset"] = Team.objects.filter(users=request.user)
        return super(DatabaseAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

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
            #only sysadmin can change team accountable for a database
            if request.user.has_perm(self.perm_add_database_infra):
                return ('name', 'databaseinfra') + self.readonly_fields
            else:
                return ('name', 'databaseinfra', 'team') + self.readonly_fields
        return self.readonly_fields


    def queryset(self, request):
        qs = super(DatabaseAdmin, self).queryset(request)
        if request.user.has_perm(self.perm_add_database_infra):
            return qs

        return qs.filter(team__in=[team.id for team in Team.objects.filter(users=request.user)])

    def has_add_permission(self, request):
        """User must be set to at least one team to be able to add database"""
        teams = Team.objects.filter(users=request.user)
        if not teams:
            self.message_user(request, self.database_add_perm_message, level=messages.ERROR)
            return False
        else:
            return super(DatabaseAdmin, self).has_add_permission(request)

    def changelist_view(self, request, extra_context=None):
        if request.user.has_perm(self.perm_manage_quarantine_database):
            self.list_filter = self.list_filter_advanced
            self.list_display = self.list_display_advanced
        else:
            self.list_filter = self.list_filter_basic
            self.list_display = self.list_display_basic
        
        return super(DatabaseAdmin, self).changelist_view(request, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        self.form = DatabaseForm
        
        try:
            teams = Team.objects.filter(users=request.user)
            LOG.info("user %s teams: %s" % (request.user, teams))
            if not teams:
                self.message_user(request, self.database_add_perm_message, level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:logical_database_changelist'))

            #if no team is specified and the user has only one team, then set it to the database
            if teams.count() == 1 and request.method == 'POST' and not request.user.has_perm(self.perm_add_database_infra):
                post_data = request.POST.copy()
                if 'team' in post_data:
                    post_data['team'] = u"%s" % teams[0].pk
            
                request.POST = post_data

            return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)
        except DatabaseAlreadyExists:
            self.message_user(request, _('An inconsistency was found: The database "%s" already exists in infra-structure but not in DBaaS.') % request.POST['name'], level=messages.ERROR)
            request.method = 'GET'
            return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        database = Database.objects.get(id=object_id)
        self.form = DatabaseForm
        extra_context = extra_context or {}

        if database.is_in_quarantine:
            extra_context['delete_button_name'] = self.delete_button_name
        else:
            extra_context['delete_button_name'] = "Delete"
        return super(DatabaseAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        database = Database.objects.get(id=object_id)
        extra_context = extra_context or {}
        if not database.is_in_quarantine:
            extra_context['quarantine_days'] = Configuration.get_by_name_as_int('quarantine_retention_days')
        return super(DatabaseAdmin, self).delete_view(request, object_id, extra_context=extra_context)

