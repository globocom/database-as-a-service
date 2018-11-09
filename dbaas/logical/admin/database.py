# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import sys
from dex import dex
from cStringIO import StringIO
from functools import partial
from bson.json_util import loads
from django.utils.translation import ugettext_lazy as _
from django_services import admin
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.admin.util import flatten_fieldsets
from django.core.urlresolvers import reverse
from django.conf.urls import patterns, url
from django.contrib import messages
from django.utils.html import format_html, escape
from django.forms.models import modelform_factory
from django.core.exceptions import FieldError
from dbaas import constants
from account.models import Team
from drivers.errors import DatabaseAlreadyExists
from notification.tasks import TaskRegister
from system.models import Configuration
from util.html import show_info_popup
from logical.models import Database
from logical.views import database_details, database_hosts, \
    database_credentials, database_resizes, database_backup, database_dns, \
    database_metrics, database_destroy, database_delete_host, \
    database_upgrade, database_upgrade_retry, database_resize_retry, \
    database_resize_rollback, database_make_backup, \
    database_change_parameters, database_change_parameters_retry, \
    database_switch_write, database_reinstall_vm, database_reinstall_vm_retry,\
    DatabaseParameters, database_configure_ssl_retry, database_configure_ssl, \
    database_migrate

from logical.forms import DatabaseForm
from logical.service.database import DatabaseService

LOG = logging.getLogger(__name__)


class DatabaseAdmin(admin.DjangoServicesAdmin):

    """
    the form used by this view is returned by the method get_form
    """

    database_add_perm_message = _(
        "You must be set to at least one team to add a database, and the service administrator has been notified about this.")
    perm_manage_quarantine_database = constants.PERM_MANAGE_QUARANTINE_DATABASE
    perm_add_database_infra = constants.PERM_ADD_DATABASE_INFRA

    service_class = DatabaseService
    search_fields = (
        "name", "databaseinfra__name", "team__name", "project__name",
        "environment__name", "databaseinfra__engine__engine_type__name"
    )
    list_display_basic = [
        "name_html", "team_admin_page", "engine_html", "environment",
        "offering_html", "friendly_status", "created_dt_format"
    ]
    list_display_advanced = list_display_basic + ["quarantine_dt_format"]
    list_filter_basic = [
        "project", "databaseinfra__environment", "databaseinfra__engine",
        "databaseinfra__plan", "databaseinfra__engine__engine_type", "status",
        "databaseinfra__plan__has_persistence", "databaseinfra__plan__replication_topology__name",
        "databaseinfra__ssl_configured"
    ]
    list_filter_advanced = list_filter_basic + ["is_in_quarantine", "team"]
    add_form_template = "logical/database/database_add_form.html"
    delete_button_name = "Delete"
    fieldsets_add = (
        (None, {
            'fields': (
                'name', 'description', 'project', 'environment', 'engine',
                'team', 'team_contact', 'subscribe_to_email_events', 'plan',
                'is_in_quarantine',
            )
        }
        ),
    )
    actions = None

    def quarantine_dt_format(self, database):
        return database.quarantine_dt or ""

    quarantine_dt_format.short_description = "Quarantine since"
    quarantine_dt_format.admin_order_field = 'quarantine_dt'

    def created_dt_format(self, database):
        return database.created_at.strftime("%b. %d, %Y") or ""

    created_dt_format.short_description = "Created at"
    created_dt_format.admin_order_field = 'created_at'

    def environment(self, database):
        return database.environment

    environment.admin_order_field = 'name'

    def plan(self, database):
        return database.plan

    plan.admin_order_field = 'name'

    def friendly_status(self, database):
        return database.status_html

    friendly_status.short_description = "Status"

    def team_admin_page(self, database):
        team_name = database.team.name
        if self.list_filter == self.list_filter_advanced:
            url = reverse('admin:account_team_change',
                          args=(database.team.id,))
            team_name = """<a href="{}"> {} </a> """.format(url, team_name)
            return format_html(team_name)
        return team_name

    team_admin_page.short_description = "Team"

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
            ed_point = escape(database.get_endpoint_dns())
        except:
            ed_point = None
        return show_info_popup(
            database.name, "Show Endpoint", ed_point,
            "icon-info-sign", "show-endpoint"
        )
    name_html.short_description = _("name")
    name_html.admin_order_field = "name"

    def engine_type(self, database):
        return database.engine_type
    engine_type.admin_order_field = 'name'

    def engine_html(self, database):
        engine_info = str(database.engine)

        topology = database.databaseinfra.plan.replication_topology
        if topology.details:
            engine_info += " - " + topology.details

        upgrades = database.upgrades.filter(source_plan=database.infra.plan)
        last_upgrade = upgrades.last()
        if not(last_upgrade and last_upgrade.is_status_error):
            return engine_info

        upgrade_url = reverse('admin:maintenance_databaseupgrade_change', args=[last_upgrade.id])
        task_url = reverse('admin:notification_taskhistory_change', args=[last_upgrade.task.id])
        retry_url = database.get_upgrade_retry_url()
        upgrade_content = \
            "<a href='{}' target='_blank'>Last upgrade</a> has an <b>error</b>, " \
            "please check the <a href='{}' target='_blank'>task</a> and " \
            "<a href='{}'>retry</a> the database upgrade".format(
                upgrade_url, task_url, retry_url
            )
        return show_info_popup(
            engine_info, "Database Upgrade", upgrade_content,
            icon="icon-warning-sign", css_class="show-upgrade"
        )
    engine_html.short_description = _("engine")
    engine_html.admin_order_field = "databaseinfra__engine"

    def offering_html(self, database):
        last_resize = database.resizes.last()
        last_reinstallvm = database.reinstall_vm.last()
        if last_resize and last_resize.is_status_error:
            resize_url = reverse('admin:maintenance_databaseresize_change', args=[last_resize.id])
            task_url = reverse('admin:notification_taskhistory_change', args=[last_resize.task.id])
            retry_url = database.get_resize_retry_url()
            rollback_url = database.get_resize_rollback_url()
            resize_content = \
                "<a href='{}' target='_blank'>Last resize</a> has an <b>error</b>, " \
                "please check the <a href='{}' target='_blank'>task</a> and " \
                "<a href='{}'>retry</a> or <a href='{}'>rollback</a> the database resize".format(
                    resize_url, task_url, retry_url, rollback_url
                )
            return show_info_popup(
                database.offering, "Database Resize", resize_content,
                icon="icon-warning-sign", css_class="show-resize"
            )
        elif last_reinstallvm and last_reinstallvm.is_status_error:
            reinstallvm_url = reverse('admin:maintenance_databasereinstallvm_change', args=[last_reinstallvm.id])
            task_url = reverse('admin:notification_taskhistory_change', args=[last_reinstallvm.task.id])
            retry_url = database.get_reinstallvm_retry_url()
            reinstallvm_content = \
                "<a href='{}' target='_blank'>Last reinstall VM</a> has an <b>error</b>, " \
                "please check the <a href='{}' target='_blank'>task</a> and " \
                "<a href='{}'>retry</a> the database reinstall vm".format(
                    reinstallvm_url, task_url, retry_url
                )
            return show_info_popup(
                database.offering, "Database Reinstall VM", reinstallvm_content,
                icon="icon-warning-sign", css_class="show-resize"
            )
        else:
            return database.databaseinfra.offering

    offering_html.short_description = _("offering")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        filter teams for the ones that the user is associated, unless the user has ther
        perm to add databaseinfra. In this case, he should see all teams.
        """
        if not request.user.has_perm(self.perm_add_database_infra):
            if db_field.name == "team":
                kwargs["queryset"] = Team.objects.filter(users=request.user)
        return super(DatabaseAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def queryset(self, request):
        qs = super(DatabaseAdmin, self).queryset(request)
        if request.user.has_perm(self.perm_add_database_infra):
            return qs

        return qs.filter(team__in=[team.id for team in Team.objects.filter(users=request.user)])

    def has_add_permission(self, request):
        """User must be set to at least one team to be able to add database"""
        teams = Team.objects.filter(users=request.user)
        if not teams:
            self.message_user(
                request, self.database_add_perm_message, level=messages.ERROR)
            return False
        else:
            return super(DatabaseAdmin, self).has_add_permission(request)

    def get_form(self, request, obj=None, **kwargs):
        if 'fields' in kwargs:
            fields = kwargs.pop('fields')
        else:
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        exclude.extend(self.get_readonly_fields(request, obj))
        if self.exclude is None and hasattr(self.form, '_meta') and self.form._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # ModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        # if exclude is an empty list we pass None to be consistent with the
        # default on modelform_factory
        exclude = exclude or None

        defaults = {
            "form": self.form,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)

        try:
            return modelform_factory(self.model, **defaults)
        except FieldError as e:
            raise FieldError('%s. Check fields/fieldsets/exclude attributes of class %s.'
                             % (e, self.__class__.__name__))

    def changelist_view(self, request, extra_context=None):
        if request.user.has_perm(self.perm_manage_quarantine_database):
            self.list_display = self.list_display_advanced
        else:
            self.list_display = self.list_display_basic

        if request.user.has_perm(self.perm_add_database_infra):
            self.list_filter = self.list_filter_advanced
        else:
            self.list_filter = self.list_filter_basic

        return super(DatabaseAdmin, self).changelist_view(request, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        self.form = DatabaseForm

        try:

            if request.method == 'POST':

                teams = Team.objects.filter(users=request.user)
                LOG.info("user %s teams: %s" % (request.user, teams))
                if not teams:
                    self.message_user(
                        request, self.database_add_perm_message,
                        level=messages.ERROR
                    )
                    return HttpResponseRedirect(
                        reverse('admin:logical_database_changelist')
                    )

                # if no team is specified and the user has only one team, then
                # set it to the database
                if teams.count() == 1 and request.method == 'POST' and not request.user.has_perm(
                        self.perm_add_database_infra):

                    post_data = request.POST.copy()
                    if 'team' in post_data:
                        post_data['team'] = u"%s" % teams[0].pk

                    request.POST = post_data

                form = DatabaseForm(request.POST)

                if not form.is_valid():
                    return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)

                database_creation_message = "call create_database - name={}, plan={}, environment={}, team={}, project={}, description={}, user={}, subscribe_to_email_events {}".format(
                    form.cleaned_data['name'], form.cleaned_data['plan'],
                    form.cleaned_data['environment'], form.cleaned_data['team'],
                    form.cleaned_data['project'], form.cleaned_data['description'],
                    request.user, form.cleaned_data['subscribe_to_email_events']
                )
                LOG.debug(database_creation_message)

                TaskRegister.database_create(
                    name=form.cleaned_data['name'],
                    plan=form.cleaned_data['plan'],
                    environment=form.cleaned_data['environment'],
                    team=form.cleaned_data['team'],
                    project=form.cleaned_data['project'],
                    description=form.cleaned_data['description'],
                    subscribe_to_email_events=form.cleaned_data['subscribe_to_email_events'],
                    user=request.user
                )
                url = reverse('admin:notification_taskhistory_changelist')
                # Redirect after POST
                return HttpResponseRedirect(url + "?user=%s" % request.user.username)

            else:
                return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)

        except DatabaseAlreadyExists:
            self.message_user(request, _(
                'An inconsistency was found: The database "%s" already exists in infra-structure but not in DBaaS.') %
                request.POST['name'], level=messages.ERROR)

            request.method = 'GET'
            return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        database = Database.objects.get(id=object_id)

        can_be_deleted, error = database.can_be_deleted()
        if not can_be_deleted:
            self.message_user(request, error, level=messages.ERROR)
            url = '/admin/logical/database/{}/'.format(object_id)
            return HttpResponseRedirect(url)

        extra_context = extra_context or {}
        if not database.is_in_quarantine:
            extra_context['quarantine_days'] = Configuration.get_by_name_as_int('quarantine_retention_days')

        return super(DatabaseAdmin, self).delete_view(request, object_id, extra_context=extra_context)

    def delete_model(modeladmin, request, obj):
        LOG.debug("Deleting {}".format(obj))
        database = obj

        can_be_deleted, error = database.can_be_deleted()
        if not can_be_deleted:
            modeladmin.message_user(request, error, level=messages.ERROR)
            url = reverse('admin:logical_database_changelist')
            return HttpResponseRedirect(url)

        database.destroy(request.user)

    def database_dex_analyze_view(self, request, database_id):
        import os
        import string

        def generate_random_string(length, stringset=string.ascii_letters + string.digits):
            return ''.join([stringset[i % len(stringset)]
                            for i in [ord(x) for x in os.urandom(length)]])

        database = Database.objects.get(id=database_id)

        if database.status != Database.ALIVE or not database.database_status.is_alive:
            self.message_user(
                request, "Database is not alive cannot be analyzed", level=messages.ERROR)
            url = reverse('admin:logical_database_changelist')
            return HttpResponseRedirect(url)

        if database.is_being_used_elsewhere():
            self.message_user(
                request, "Database cannot be analyzed because it is in use by another task.", level=messages.ERROR)
            url = reverse('admin:logical_database_changelist')
            return HttpResponseRedirect(url)

        parsed_logs = ''

        arq_path = Configuration.get_by_name(
            'database_clone_dir') + '/' + database.name + generate_random_string(20) + '.txt'

        arq = open(arq_path, 'w')
        arq.write(parsed_logs)
        arq.close()

        uri = 'mongodb://{}:{}@{}:{}/admin'.format(database.databaseinfra.user,
                                                   database.databaseinfra.password,
                                                   database.databaseinfra.instances.all()[
                                                       0].address,
                                                   database.databaseinfra.instances.all()[0].port)

        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        md = dex.Dex(db_uri=uri, verbose=False, namespaces_list=[],
                     slowms=0, check_indexes=True, timeout=0)

        md.analyze_logfile(arq_path)

        sys.stdout = old_stdout

        dexanalyzer = loads(
            mystdout.getvalue().replace("\"", "&&").replace("'", "\"").replace("&&", "'"))

        os.remove(arq_path)

        import ast
        final_mask = """<div>"""

        for result in dexanalyzer['results']:

            final_mask += "<h3> Collection: " + result['namespace'] + "</h3>"
            final_mask += \
                """<li> Query: """ +\
                str(ast.literal_eval(result['queryMask'])['$query']) +\
                """</li>""" +\
                """<li> Index: """ +\
                result['recommendation']['index'] +\
                """</li>""" +\
                """<li> Command: """ +\
                result['recommendation']['shellCommand'] +\
                """</li>"""

            final_mask += """<br>"""

        final_mask += """</ul> </div>"""

        return render_to_response("logical/database/dex_analyze.html", locals(), context_instance=RequestContext(request))

    def mongodb_engine_version_upgrade(self, request, database_id):

        url = reverse('admin:logical_database_change', args=[database_id])

        database = Database.objects.get(id=database_id)
        if database.is_in_quarantine:
            self.message_user(request, "Database in quarantine and cannot be upgraded!", level=messages.ERROR)
            return HttpResponseRedirect(url)

        if database.status != Database.ALIVE or not database.database_status.is_alive:
            self.message_user(request, "Database is dead and cannot be upgraded!", level=messages.ERROR)
            return HttpResponseRedirect(url)

        if database.is_being_used_elsewhere():
            self.message_user(
                request,
                "Database is being used by another task, "
                "please check your tasks",
                level=messages.ERROR
            )
            return HttpResponseRedirect(url)

        if not database.is_mongodb_24:
            self.message_user(
                request,
                "Database {} cannot be upgraded. Please contact you DBA".format(database.name),
                level=messages.ERROR
            )
            return HttpResponseRedirect(url)

        if not request.user.has_perm(constants.PERM_UPGRADE_MONGO24_TO_30):
            self.message_user(
                request,
                "You have no permissions to upgrade {}. Please, contact your DBA".format(database.name),
                level=messages.ERROR
            )
            return HttpResponseRedirect(url)

        TaskRegister.upgrade_mongodb_24_to_30(
            database=database, user=request.user
        )
        url = reverse('admin:notification_taskhistory_changelist')

        return HttpResponseRedirect(url)

    # Create your views here.
    def get_urls(self):
        urls = super(DatabaseAdmin, self).get_urls()
        my_urls = patterns(
            '',

            url(r'^/?(?P<database_id>\d+)/dex/$',
                self.admin_site.admin_view(self.database_dex_analyze_view),
                name="database_dex_analyze_view"),

            url(r'^/?(?P<database_id>\d+)/mongodb_engine_version_upgrade/$',
                self.admin_site.admin_view(
                    self.mongodb_engine_version_upgrade),
                name="mongodb_engine_version_upgrade"),

            url(
                r'^/?(?P<id>\d+)/upgrade/$',
                self.admin_site.admin_view(database_upgrade), name="upgrade"
            ),

            url(
                r'^/?(?P<id>\d+)/upgrade_retry/$',
                self.admin_site.admin_view(database_upgrade_retry),
                name="upgrade_retry"
            ),
            url(
                r'^/?(?P<id>\d+)/resize_retry/$',
                self.admin_site.admin_view(database_resize_retry),
                name="resize_retry"
            ),
            url(
                r'^/?(?P<id>\d+)/resize_rollback/$',
                self.admin_site.admin_view(database_resize_rollback),
                name="resize_rollback"
            ),
            url(
                r'^/?(?P<id>\d+)/make_backup/$',
                self.admin_site.admin_view(database_make_backup),
                name="logical_database_make_backup"
            ),

            url(
                r'^/?(?P<id>\d+)/$',
                self.admin_site.admin_view(database_details),
                name="logical_database_details"
            ),
            url(
                r'^/?(?P<id>\d+)/credentials/$',
                self.admin_site.admin_view(database_credentials),
                name="logical_database_credentials"
            ),
            url(
                r'^/?(?P<id>\d+)/hosts/$',
                self.admin_site.admin_view(database_hosts),
                name="logical_database_hosts"
            ),
            url(
                r'^/?(?P<database_id>\d+)/hosts/(?P<host_id>\d+)/delete/$',
                self.admin_site.admin_view(database_delete_host),
                name="logical_database_host_delete"
            ),
            url(
                r'^/?(?P<id>\d+)/resizes/$',
                self.admin_site.admin_view(database_resizes),
                name="logical_database_resizes"
            ),
            url(
                r'^/?(?P<id>\d+)/backup/$',
                self.admin_site.admin_view(database_backup),
                name="logical_database_backup"
            ),
            url(
                r'^/?(?P<id>\d+)/dns/$',
                self.admin_site.admin_view(database_dns),
                name="logical_database_dns"
            ),
            url(
                r'^/?(?P<id>\d+)/metrics/$',
                self.admin_site.admin_view(database_metrics),
                name="logical_database_metrics"
            ),
            url(
                r'^/?(?P<id>\d+)/destroy/$',
                self.admin_site.admin_view(database_destroy),
                name="logical_database_destroy"
            ),
            url(
                r'^/?(?P<id>\d+)/parameters/$',
                self.admin_site.admin_view(DatabaseParameters.as_view()),
                name="logical_database_parameters"
            ),
            url(
                r'^/?(?P<id>\d+)/change_parameters/$',
                self.admin_site.admin_view(database_change_parameters),
                name="change_parameters"
            ),
            url(
                r'^/?(?P<id>\d+)/change_parameters_retry/$',
                self.admin_site.admin_view(database_change_parameters_retry),
                name="change_parameters_retry"
            ),
            url(
                r'^/?(?P<database_id>\d+)/hosts/(?P<host_id>\d+)/switch/$',
                self.admin_site.admin_view(database_switch_write),
                name="logical_database_switch"
            ),
            url(
                r'^/?(?P<database_id>\d+)/hosts/(?P<host_id>\d+)/reinstallvm/$',
                self.admin_site.admin_view(database_reinstall_vm),
                name="logical_database_reinstallvm"
            ),
            url(
                r'^/?(?P<id>\d+)/reinstallvm_retry/$',
                self.admin_site.admin_view(database_reinstall_vm_retry),
                name="logical_database_reinstallvm_retry"
            ),
            url(
                r'^/?(?P<id>\d+)/migrate/$',
                self.admin_site.admin_view(database_migrate),
                name="logical_database_migrate"
            ),
            url(
                r'^/?(?P<id>\d+)/configure_ssl/$',
                self.admin_site.admin_view(database_configure_ssl),
                name="logical_database_configure_ssl"
            ),
            url(
                r'^/?(?P<id>\d+)/configure_ssl_retry/$',
                self.admin_site.admin_view(database_configure_ssl_retry),
                name="logical_database_configure_ssl_retry"
            ),

        )
        return my_urls + urls
