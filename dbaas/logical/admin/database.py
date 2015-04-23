# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django_services import admin
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.admin.util import flatten_fieldsets
from django.core.urlresolvers import reverse
from django.conf.urls import patterns, url
from django.contrib import messages
from django.utils.html import format_html, escape
from ..service.database import DatabaseService
from ..forms import DatabaseForm, CloneDatabaseForm, ResizeDatabaseForm
from ..models import Database
from physical.models import Plan, Host
from django.forms.models import modelform_factory, modelform_defines_fields
from account.models import Team
from drivers import DatabaseAlreadyExists
from logical.templatetags import capacity
from system.models import Configuration
from dbaas import constants
from django.db import router
from django.utils.encoding import force_text
from django.core.exceptions import PermissionDenied
from django.contrib.admin.util import get_deleted_objects, model_ngettext
from django.contrib.admin import helpers
from django.template.response import TemplateResponse
from notification.tasks import destroy_database
from notification.tasks import create_database
from notification.models import TaskHistory
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from django.core.exceptions import FieldError
from dex import dex
from cStringIO import StringIO
from functools import partial
import sys
from bson.json_util import loads

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
    search_fields = ("name", "databaseinfra__name", "team__name",
                            "project__name", "environment__name", "databaseinfra__engine__engine_type__name")
    list_display_basic = ["name_html", "engine_type", "environment", "plan", "friendly_status", "clone_html" ,
                          "get_capacity_html", "metrics_html", ]
    list_display_advanced = list_display_basic + ["quarantine_dt_format"]
    list_filter_basic = ["project", "databaseinfra__environment", "databaseinfra__engine", "databaseinfra__plan"]
    list_filter_advanced = list_filter_basic + ["databaseinfra", "is_in_quarantine", "team"]
    add_form_template = "logical/database/database_add_form.html"
    change_form_template = "logical/database/database_change_form.html"
    delete_button_name = "Delete"
    fieldsets_add = (
        (None, {
            'fields': ('name', 'description', 'project', 'engine', 'environment', 'team', 'plan', 'is_in_quarantine', )
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
    # actions = ['delete_mode']

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

    def friendly_status(self, database):

        html_ok = '<span class="label label-success">Alive</span>'
        html_nook = '<span class="label label-important">Dead</span>'

        if database.status == Database.ALIVE:
            return format_html(html_ok)
        else:
            return format_html(html_nook)

    friendly_status.short_description = "Status"

    def clone_html(self, database):
        html = []

        if database.is_in_quarantine or database.status != database.ALIVE:
            html.append("N/A")
        else:
            html.append("<a class='btn btn-info' href='%s'><i class='icon-file icon-white'></i></a>" % reverse(
                'admin:database_clone', args=(database.id,)))

        return format_html("".join(html))

    clone_html.short_description = "Clone"

    def metrics_html(self, database):
        html = []
        if database.databaseinfra.plan.provider == Plan.PREPROVISIONED:
            html.append("N/A")
        else:
            html.append("<a class='btn btn-info' href='%s'><i class='icon-list-alt icon-white'></i></a>" % reverse(
                'admin:database_metrics', args=(database.id,)))

        return format_html("".join(html))

    metrics_html.short_description = "Metrics"

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
        if obj:  # In edit mode
            if request.user.has_perm(self.perm_manage_quarantine_database):
                self.fieldsets_change = self.fieldsets_change_advanced
            else:
                self.fieldsets_change = self.fieldsets_change_basic

        return self.fieldsets_change if obj else self.fieldsets_add

    def get_readonly_fields(self, request, obj=None):
        """
        if in edit mode, name is readonly.
        """
        if obj:  # In edit mode
            #only sysadmin can change team accountable for a database
            if request.user.has_perm(self.perm_add_database_infra):
                return ('name', 'databaseinfra', ) + self.readonly_fields
            else:
                return ('name', 'databaseinfra', 'team',) + self.readonly_fields
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

        if obj and obj.plan.provider==Plan.CLOUDSTACK:
            if 'offering' in self.fieldsets_change[0][1]['fields'] and 'offering' in self.form.declared_fields:
                del self.form.declared_fields['offering']
            else:
                self.fieldsets_change[0][1]['fields'].append('offering')

            DatabaseForm.setup_offering_field(form=self.form,db_instance=obj)


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
                    self.message_user(request, self.database_add_perm_message, level=messages.ERROR)
                    return HttpResponseRedirect(reverse('admin:logical_database_changelist'))

                # if no team is specified and the user has only one team, then set it to the database
                if teams.count() == 1 and request.method == 'POST' and not request.user.has_perm(
                    self.perm_add_database_infra):
                    post_data = request.POST.copy()
                    if 'team' in post_data:
                        post_data['team'] = u"%s" % teams[0].pk

                    request.POST = post_data

                form = DatabaseForm(request.POST)

                if not form.is_valid():
                    return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)


                LOG.debug(
                    "call create_database - name=%s, plan=%s, environment=%s, team=%s, project=%s, description=%s, user=%s" % (
                        form.cleaned_data['name'], form.cleaned_data['plan'], form.cleaned_data['environment'],
                        form.cleaned_data['team'], form.cleaned_data['project'], form.cleaned_data['description'],
                        request.user))

                task_history = TaskHistory()
                task_history.task_name="create_database"
                task_history.task_status= task_history.STATUS_WAITING
                task_history.arguments="Database name: {}".format(form.cleaned_data['name'])
                task_history.user= request.user
                task_history.save()

                create_database.delay(name=form.cleaned_data['name'],
                                               plan=form.cleaned_data['plan'],
                                               environment=form.cleaned_data['environment'],
                                               team=form.cleaned_data['team'],
                                               project=form.cleaned_data['project'],
                                               description=form.cleaned_data['description'],
                                               task_history=task_history,
                                               user=request.user)

                url = reverse('admin:notification_taskhistory_changelist')
                return HttpResponseRedirect(url + "?user=%s" % request.user.username)  # Redirect after POST

            else:
                return super(DatabaseAdmin, self).add_view(request, form_url, extra_context=extra_context)

        except DatabaseAlreadyExists:
            self.message_user(request, _(
                'An inconsistency was found: The database "%s" already exists in infra-structure but not in DBaaS.') %
                              request.POST['name'], level=messages.ERROR)
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

    def delete_model(modeladmin, request, obj):

        LOG.debug("Deleting {}".format(obj))
        database = obj
        if database.is_in_quarantine:

            if database.plan.provider == database.plan.CLOUDSTACK:

                LOG.debug(
                    "call destroy_database - name=%s, team=%s, project=%s, user=%s" % (
                        database.name, database.team, database.project, request.user))

                task_history = TaskHistory()
                task_history.task_name="destroy_database"
                task_history.task_status= task_history.STATUS_WAITING
                task_history.arguments="Database name: {}".format(database.name)
                task_history.user= request.user
                task_history.save()

                destroy_database.delay(database=database,
                                                    task_history=task_history,
                                                    user=request.user
                                                    )

                url = reverse('admin:notification_taskhistory_changelist')
            else:
                database.delete()
        else:
            database.delete()

    def clone_view(self, request, database_id):
        database = Database.objects.get(id=database_id)
        if database.is_in_quarantine:
            self.message_user(request, "Database in quarantine cannot be cloned", level=messages.ERROR)
            url = reverse('admin:logical_database_changelist')
            return HttpResponseRedirect(url)  # Redirect after POST

        form = None
        if request.method == 'POST':  # If the form has been submitted...
            form = CloneDatabaseForm(request.POST)  # A form bound to the POST data
            if form.is_valid():  # All validation rules pass
                # Process the data in form.cleaned_data
                database_clone = form.cleaned_data['database_clone']
                plan = form.cleaned_data['plan']
                environment= form.cleaned_data['environment']

                Database.clone(database=database, clone_name=database_clone,
                                        plan=plan, environment=environment,
                                        user=request.user
                                        )

                url = reverse('admin:notification_taskhistory_changelist')
                return HttpResponseRedirect(url + "?user=%s" % request.user.username)  # Redirect after POST
        else:
            form = CloneDatabaseForm(initial={"origin_database_id": database_id})  # An unbound form
        return render_to_response("logical/database/clone.html",
                                  locals(),
                                  context_instance=RequestContext(request))

    def metricdetail_view(self, request, database_id):
        from util.metrics.metrics import get_metric_datapoints_for

        if request.method == 'GET':
            hostname = request.GET.get('hostname')
            metricname = request.GET.get('metricname')

        database = Database.objects.get(id=database_id)
        engine = database.infra.engine_name
        db_name = database.name
        URL = get_credentials_for(environment=database.environment, credential_type=CredentialType.GRAPHITE).endpoint
        graph_data = get_metric_datapoints_for(engine, db_name, hostname, url=URL, metric_name=metricname)

        title = "{} {} Metric".format(database.name, graph_data[0]["graph_name"])


        return render_to_response("logical/database/metrics/metricdetail.html", locals(), context_instance=RequestContext(request))

    def metrics_view(self, request, database_id):
        database = Database.objects.get(id=database_id)
        instance = database.infra.instances.all()[0]

        if request.method == 'GET':
            hostname = request.GET.get('hostname')

        if hostname is None:
            hostname = instance.hostname.hostname.split('.')[0]

        return self.database_host_metrics_view(request, database, hostname)

    def database_host_metrics_view(self, request, database, hostname):
        from util.metrics.metrics import get_metric_datapoints_for
        URL = get_credentials_for(environment=database.environment, credential_type=CredentialType.GRAPHITE).endpoint

        title = "{} Metrics".format(database.name)

        if request.method == 'GET':
            engine = database.infra.engine_name
            db_name = database.name
            hosts = []

            for host in Host.objects.filter(instance__databaseinfra=database.infra).distinct():
                hosts.append(host.hostname.split('.')[0])

            graph_data = get_metric_datapoints_for(engine, db_name, hostname, url=URL)

        return render_to_response("logical/database/metrics/metrics.html", locals(), context_instance=RequestContext(request))

    def database_dex_analyze_view(self, request, database_id):
        database = Database.objects.get(id=database_id)

        uri = 'mongodb://{}:{}@{}:{}/admin'.format(database.databaseinfra.user,
                                                   database.databaseinfra.password,
                                                   database.databaseinfra.instances.all()[0].address,
                                                   #'10.236.1.15',
                                                   database.databaseinfra.instances.all()[0].port)

        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        md = dex.Dex(db_uri = uri, verbose=False, namespaces_list = [], slowms=0, check_indexes=True, timeout=0)
        md.analyze_profile()

        sys.stdout = old_stdout

        dexanalyzer = loads(mystdout.getvalue().replace("\"", "&&").replace("'", "\"").replace("&&","'"))

        import ast
        final_mask = """<div>"""

        for result in dexanalyzer['results']:

                final_mask += "<h3> Collection: " + result['namespace']+ "</h3>"
                final_mask += \
                             """<li> Query: """ +\
                            str(ast.literal_eval(result['queryMask'])['$query']) +\
                            """</li>""" +\
                            """<li> Index: """+\
                            result['recommendation']['index']+\
                            """</li>"""+\
                            """<li> Command: """+\
                            result['recommendation']['shellCommand']+\
                            """</li>"""

                final_mask += """<br>"""

        final_mask += """</ul> </div>"""


        return render_to_response("logical/database/dex_analyze.html", locals(), context_instance=RequestContext(request))

    def database_resize_view(self, request, database_id):
        from dbaas_cloudstack.models import CloudStackPack

        database = Database.objects.get(id=database_id)

        url = reverse('admin:logical_database_change', args=[database.id])

        if database.is_in_quarantine:
            self.message_user(request, "Database in quarantine and cannot be resized", level=messages.ERROR)
            return HttpResponseRedirect(url)  # Redirect after POST

        if not database.database_status.is_alive:
            self.message_user(request, "Database is dead  and cannot be resized", level=messages.ERROR)
            return HttpResponseRedirect(url)  # Redirect after POST

        if not CloudStackPack.objects.filter(
                                                                offering__region__environment=database.environment,
                                                                engine_type__name= database.engine_type
                                                            ).exclude(offering__serviceofferingid=database.offering_id):
            self.message_user(request, "Database has no offerings availables.", level=messages.ERROR)
            return HttpResponseRedirect(url)  # Redirect after POST


        form = None
        if request.method == 'POST':  # If the form has been submitted...
            form = ResizeDatabaseForm(request.POST, initial={"database_id": database_id, "original_offering_id": database.offering_id},)  # A form bound to the POST data
            if form.is_valid():  # All validation rules pass

                cloudstackpack = CloudStackPack.objects.get(id=request.POST.get('target_offer'))
                Database.resize(database=database, cloudstackpack=cloudstackpack,
                                        user=request.user,)

                url = reverse('admin:notification_taskhistory_changelist')

                return HttpResponseRedirect(url + "?user=%s" % request.user.username)  # Redirect after POST
        else:
            form = ResizeDatabaseForm(initial={"database_id": database_id, "original_offering_id": database.offering_id},)  # An unbound form
        return render_to_response("logical/database/resize.html",
                                  locals(),
                                  context_instance=RequestContext(request))

    def database_log_view(self, request, database_id):

        database = Database.objects.get(id=database_id)
        instance = database.infra.instances.all()[0]

#        if request.method == 'GET':
#            hostname = request.GET.get('hostname')
#
#        if hostname is None:
#            hostname = instance.hostname.hostname.split('.')[0]
#
        return render_to_response("logical/database/lognit.html",
                                  locals(),
                                  context_instance=RequestContext(request))

    def get_urls(self):
        urls = super(DatabaseAdmin, self).get_urls()
        my_urls = patterns('',
                           url(r'^/?(?P<database_id>\d+)/clone/$', self.admin_site.admin_view(self.clone_view),
                               name="database_clone"),

                           url(r'^/?(?P<database_id>\d+)/metrics/$', self.admin_site.admin_view(self.metrics_view),
                               name="database_metrics"),

                           url(r'^/?(?P<database_id>\d+)/metricdetail/$', self.admin_site.admin_view(self.metricdetail_view),
                               name="database_metricdetail"),

                           url(r'^/?(?P<database_id>\d+)/resize/$', self.admin_site.admin_view(self.database_resize_view),
                               name="database_resize"),

                           url(r'^/?(?P<database_id>\d+)/lognit/$', self.admin_site.admin_view(self.database_log_view),
                               name="database_resize"),

                           url(r'^/?(?P<database_id>\d+)/dex/$', self.admin_site.admin_view(self.database_dex_analyze_view),
                               name="database_dex_analyze_view"),

        )

        return my_urls + urls

    def delete_selected(self, request, queryset):
        opts = self.model._meta
        app_label = opts.app_label

        # Check that the user has delete permission for the actual model
        if not self.has_delete_permission(request):
            raise PermissionDenied

        using = router.db_for_write(self.model)

        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, self.admin_site, using)

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if request.POST.get('post'):
            if perms_needed:
                raise PermissionDenied

            n = queryset.count()
            quarantine =any(result['is_in_quarantine']==True for result in queryset.values('is_in_quarantine'))

            if n:
                for obj in queryset:
                    obj_display = force_text(obj)
                    self.log_deletion(request, obj, obj_display)
                    #remove the object
                    self.delete_model(request, obj)

                self.message_user(request, _("Successfully deleted %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(self.opts, n)
                })
            # Return None to display the change list page again.
            if quarantine:
                url = reverse('admin:notification_taskhistory_changelist')
                return HttpResponseRedirect(url + "?user=%s" % request.user.username)

            return None

        if len(queryset) == 1:
            objects_name = force_text(opts.verbose_name)
        else:
            objects_name = force_text(opts.verbose_name_plural)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": objects_name}
        else:
            title = _("Are you sure?")

        context = {
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }

        # Display the confirmation page

        return TemplateResponse(request, self.delete_selected_confirmation_template or [
            "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/delete_selected_confirmation.html" % app_label,
            "admin/delete_selected_confirmation.html"
        ], context, current_app=self.admin_site.name)
