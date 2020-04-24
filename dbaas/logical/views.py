# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import datetime
import json
from collections import OrderedDict
from operator import itemgetter
import logging
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.detail import BaseDetailView
from django.views.generic import TemplateView, RedirectView, View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext

from dbaas_credentials.models import CredentialType
from dbaas import constants
from account.models import Team
from drivers.errors import CredentialAlreadyExists
from physical.models import (
    Host, DiskOffering, Environment, Plan, Offering,
    EnginePatch
)
from util import get_credentials_for
from notification.tasks import TaskRegister, execute_scheduled_maintenance
from notification.models import TaskHistory
from system.models import Configuration
from logical.errors import DisabledDatabase
from logical.forms.database import DatabaseDetailsForm, DatabaseForm
from logical.models import Credential, Database, Project
from logical.validators import (check_is_database_enabled,
                                check_is_database_dead,
                                ParameterValidator)
from workflow.steps.util.host_provider import Provider
from maintenance.models import (
    DatabaseUpgradePatch, DatabaseUpgrade, TaskSchedule, DatabaseMigrateEngine,
    RecreateSlave, AddInstancesToDatabase
)
from . import services
from . import exceptions
from . import utils


LOG = logging.getLogger(__name__)


def credential_parameter_by_name(request, env_id, param_name):

    try:
        env = Environment.objects.get(id=env_id)
        credential = get_credentials_for(
            env, CredentialType.HOST_PROVIDER
        )
    except (IndexError, Environment.DoesNotExist):
        msg = ''
    else:
        msg = credential.get_parameter_by_name(param_name)

    output = json.dumps({'msg': msg or ''})
    return HttpResponse(output, content_type="application/json")


class CredentialBase(BaseDetailView):
    model = Credential

    def check_permission(self, request, perm, obj):
        if not request.user.has_perm(perm, obj=obj):
            raise PermissionDenied

    def as_json(self, obj):
        if isinstance(obj, Credential):
            obj = {
                "credential": {
                    "user": obj.user,
                    "password": obj.password,
                    "pk": obj.pk,
                    "ssl_swap_label": obj.ssl_swap_label,
                    "force_ssl": obj.force_ssl,
                    "privileges": obj.privileges,
                }
            }
        output = json.dumps(obj, indent=4)
        return HttpResponse(output, content_type="application/json")


class CredentialView(CredentialBase):

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", None)
        database_id = request.POST.get("database_id", None)
        privileges = request.POST.get("privileges", None)

        try:
            database = get_object_or_404(Database, pk=database_id)

            # check permission
            self.check_permission(request, "logical.add_credential", database)
            credential = Credential.create_new_credential(
                username, database, privileges
            )
            return self.as_json(credential)
        except CredentialAlreadyExists:
            return self.as_json({"error": "credential already exists"})
        except ValidationError as e:
            return self.as_json({"error": ", ".join(e.messages)})

    @method_decorator(csrf_exempt)
    def put(self, request, *args, **kwargs):
        credential = self.get_object()

        # check permission
        self.check_permission(request, "logical.change_credential", credential)

        credential.reset_password()
        return self.as_json(credential)

    @method_decorator(csrf_exempt)
    def delete(self, request, *args, **kwargs):
        credential = self.get_object()

        # check permission
        self.check_permission(request, "logical.delete_credential", credential)

        credential.delete()
        return self.as_json(credential)


class CredentialSSLView(CredentialBase):

    @method_decorator(csrf_exempt)
    def put(self, request, *args, **kwargs):
        credential = self.get_object()

        # check permission
        self.check_permission(request, "logical.change_credential", credential)

        credential.swap_force_ssl()
        return self.as_json(credential)


def check_permission(request, id, tab):
    is_dba = request.user.team_set.filter(role__name="role_dba")
    database = Database.objects.get(id=id)
    if not is_dba:
        can_access = True
        teams = request.user.team_set.all()
        if (
            database.team not in teams and
            not utils.can_access_database(database, teams)
        ):
            messages.add_message(
                request, messages.ERROR,
                ('This database belong to {} team, you are not member of '
                 "this team or has not access to database's environment").format(
                     database.team
                )
            )
            can_access = False
        elif database.is_in_quarantine:
            messages.add_message(
                request, messages.ERROR,
                'This database is in quarantine, please contact your DBA'
            )
            can_access = False
        elif tab == "migrate":
            messages.add_message(
                request, messages.ERROR, 'Only DBA can do migrate')
            can_access = False

        if not can_access:
            return HttpResponseRedirect(
                reverse('admin:logical_database_changelist')
            )

    context = {
        'database': database,
        'current_tab': tab,
        'user': request.user,
        'is_dba': is_dba
    }
    return context


def database_view(tab):
    def database_decorator(func):
        def func_wrapper(request, id):
            context = check_permission(request, id, tab)
            if isinstance(context, dict):
                return func(request, context, context['database'])
            return context
        return func_wrapper
    return database_decorator


# TODO: RESOLVER ESSE CONFLITO COM O DECORATOR DE CIMA
def database_view_class(tab):
    def database_decorator(func):
        def func_wrapper(self, request, id):
            context = check_permission(request, id, tab)

            return func(self, request, context, context['database'])
        return func_wrapper
    return database_decorator


def user_tasks(user):
    url = reverse('admin:notification_taskhistory_changelist')
    filter = "user={}".format(user.username)
    return '{}?{}'.format(url, filter)


def refresh_status(request, database_id):
    try:
        database = Database.objects.get(id=database_id)
    except (Database.DoesNotExist, ValueError):
        return
    instances_status = []
    for instance in database.infra.instances.all():
        instance.update_status()
        instances_status.append({"id": instance.hostname.id,
                                 "html": instance.status_html()})
    database.update_status()
    output = json.dumps({'database_status': database.status_html,
                         'instances_status': instances_status})
    return HttpResponse(output, content_type="application/json")


@database_view('details')
def database_details(request, context, database):
    if request.method == 'POST':
        form = DatabaseDetailsForm(request.POST or None, instance=database)
        if form.is_valid():
            form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'The database "{}" was changed successfully'.format(database)
            )
            return HttpResponseRedirect(
                reverse('admin:logical_database_changelist')
            )
    engine = '{}_{}'.format(
        database.engine.name,
        database.databaseinfra.engine_patch.full_version
    )
    topology = database.databaseinfra.plan.replication_topology
    engine = engine + " - " + topology.details if topology.details else engine
    try:
        masters_quant = len(database.driver.get_master_instance(
            default_timeout=True)
        )
    except TypeError:
        masters_quant = 1
    except Exception:
        masters_quant = 0

    context['masters_quant'] = masters_quant
    context['engine'] = engine
    context['projects'] = Project.objects.all()
    context['teams'] = Team.objects.all()

    return render_to_response(
        "logical/database/details/details_tab.html",
        context, RequestContext(request)
    )


@database_view('credentials')
def database_credentials(request, context, database):

    if request.method == 'POST':
        if 'setup_ssl' in request.POST:
            database_configure_ssl(request, context, database)
        elif 'retry_setup_ssl' in request.POST:
            database_configure_ssl_retry(request, context, database)

    context['can_setup_ssl'] = \
        (not database.infra.ssl_configured) and \
        database.infra.plan.replication_topology.can_setup_ssl and \
        request.user.has_perm(constants.PERM_CONFIGURE_SSL)

    last_configure_ssl = database.configure_ssl.last()
    context['last_configure_ssl'] = last_configure_ssl

    return render_to_response(
        "logical/database/details/credentials_tab.html",
        context, RequestContext(request)
    )


def database_configure_ssl(request, context, database):

    can_do_configure_ssl, error = database.can_do_configure_ssl()

    if not can_do_configure_ssl:
        messages.add_message(request, messages.ERROR, error)
    else:
        TaskRegister.database_configure_ssl(
            database=database,
            user=request.user
        )

    return HttpResponseRedirect(
        reverse(
            'admin:logical_database_credentials',
            kwargs={'id': database.id}
        )
    )


def database_configure_ssl_retry(request, context=None, database=None,
                                 id=None):

    if database is None:
        database = Database.objects.get(id=id)

    can_do_configure_ssl, error = database.can_do_configure_ssl_retry()

    if can_do_configure_ssl:
        last_configure_ssl = database.configure_ssl.last()
        if not last_configure_ssl:
            error = "Database does not have configure SSL task!"
        elif not last_configure_ssl.is_status_error:
            error = ("Cannot do retry, last configure SSL status "
                     "is '{}'!").format(
                        last_configure_ssl.get_status_display()
            )
        else:
            since_step = last_configure_ssl.current_step

    if error:
        messages.add_message(request, messages.ERROR, error)
    else:
        TaskRegister.database_configure_ssl(
            database=database,
            user=request.user,
            since_step=since_step
        )

    return HttpResponseRedirect(
        reverse(
            'admin:logical_database_credentials',
            kwargs={'id': database.id}
        )
    )


class DatabaseParameters(TemplateView):

    PROTECTED = 1
    EDITABLE = 2
    TASK_RUNNING = 3
    TASK_ERROR = 4
    TASK_SUCCESS = 5
    template_name = "logical/database/details/parameters_tab.html"

    @staticmethod
    def update_database_parameters(request_post, database):
        from physical.models import DatabaseInfraParameter
        from physical.models import Parameter

        error = False

        for key in request_post.keys():
            if key.startswith("new_value_"):
                parameter_new_value = request_post.get(key)
                if parameter_new_value:
                    parameter_id = key.split("new_value_")[1]
                    parameter = Parameter.objects.get(id=parameter_id)
                    if not ParameterValidator.validate_value(
                            parameter_new_value, parameter):
                        error = "Invalid Parameter Value for {}".format(
                            parameter.name
                        )
                        return None, error

        changed_parameters = []
        for key in request_post.keys():
            if key.startswith("new_value_"):
                parameter_new_value = request_post.get(key)
                if parameter_new_value:
                    parameter_id = key.split("new_value_")[1]
                    parameter = Parameter.objects.get(id=parameter_id)
                    changed = DatabaseInfraParameter.update_parameter_value(
                        databaseinfra=database.databaseinfra,
                        parameter=parameter,
                        value=parameter_new_value,
                    )
                    if changed:
                        changed_parameters.append(parameter_id)

            if key.startswith("checkbox_reset_"):
                reset_default_value = request_post.get(key)
                if reset_default_value == "on":
                    parameter_id = key.split("checkbox_reset_")[1]
                    parameter = Parameter.objects.get(id=parameter_id)
                    changed = DatabaseInfraParameter.set_reset_default(
                        databaseinfra=database.databaseinfra,
                        parameter=parameter,
                    )
                    if changed:
                        changed_parameters.append(parameter_id)

        return changed_parameters, error

    def get_form_parameters(self, database):
        from physical.models import DatabaseInfraParameter
        form_parameters = []

        topology_parameters = (
            database.plan.replication_topology.parameter.all()
        )
        databaseinfra = database.databaseinfra

        for topology_parameter in topology_parameters:
            editable_parameter = True
            default_value = databaseinfra.get_dbaas_parameter_default_value(
                parameter_name=topology_parameter.name
            )
            if not topology_parameter.dynamic:
                self.there_is_static_parameter = True

            try:
                infra_parameter = DatabaseInfraParameter.objects.get(
                    databaseinfra=databaseinfra,
                    parameter=topology_parameter
                )
            except DatabaseInfraParameter.DoesNotExist:
                current_value = '-'
                applied_on_database = True
                reset_default_value = False
            else:
                current_value = infra_parameter.value
                applied_on_database = infra_parameter.applied_on_database
                reset_default_value = infra_parameter.reset_default_value

            if self.form_status == self.TASK_ERROR:
                try:
                    infra_parameter = DatabaseInfraParameter.objects.get(
                        databaseinfra=databaseinfra,
                        parameter=topology_parameter,
                        applied_on_database=False
                    )
                except DatabaseInfraParameter.DoesNotExist:
                    editable_parameter = False
                else:
                    editable_parameter = True

            database_parameter = {
                "id": topology_parameter.id,
                "name": topology_parameter.name,
                "dynamic": topology_parameter.dynamic,
                "dbaas_default_value": default_value,
                "current_value": current_value,
                "new_value": "",
                "applied_on_database": applied_on_database,
                "reset_default_value": reset_default_value,
                "editable_parameter": editable_parameter,
                "parameter_type": topology_parameter.parameter_type,
                "allowed_values": topology_parameter.allowed_values,
                "description": topology_parameter.description,
                "engine_type": database.engine.engine_type.name,
            }
            form_parameters.append(database_parameter)

        return form_parameters

    def get_context_data(self, **kwargs):
        from physical.models import DatabaseInfraParameter

        parameters_changed_pending = DatabaseInfraParameter.objects.filter(
            databaseinfra=self.database.databaseinfra,
            applied_on_database=False
        )
        if parameters_changed_pending:
            self.form_status = self.TASK_RUNNING

        last_change_parameters = self.database.change_parameters.last()
        if last_change_parameters:
            if last_change_parameters.is_running:
                self.form_status = self.TASK_RUNNING
            elif last_change_parameters.is_status_error:
                self.form_status = self.TASK_ERROR

        form_database_parameters = self.get_form_parameters(self.database)

        self.context['form_database_parameters'] = form_database_parameters
        self.context['static_parameter'] = self.there_is_static_parameter
        self.context['PROTECTED'] = self.PROTECTED
        self.context['EDITABLE'] = self.EDITABLE
        self.context['TASK_RUNNING'] = self.TASK_RUNNING
        self.context['TASK_ERROR'] = self.TASK_ERROR
        self.context['TASK_SUCCESS'] = self.TASK_SUCCESS
        self.context['form_status'] = self.form_status
        self.context['last_change_parameters'] = last_change_parameters

        return self.context

    def post(self, request, *args, **kwargs):

        context, database = args

        if 'edit_parameters' in request.POST:
            self.form_status = self.EDITABLE
            return self.get(request)

        if 'cancel_edit_parameters' in request.POST:
            self.form_status = self.PROTECTED
            return self.get(request)

        if 'retry_update_parameters' in request.POST:
            self.form_status = self.TASK_ERROR
            can_do_change_parameters_retry, error = (
                database.can_do_change_parameters_retry()
            )
            if not can_do_change_parameters_retry:
                messages.add_message(request, messages.ERROR, error)
                return self.get(request)
            else:
                changed_parameters, error = self.update_database_parameters(
                    request.POST, database
                )
                if error:
                    messages.add_message(request, messages.ERROR, error)
                    return self.get(request)
                return HttpResponseRedirect(
                    reverse('admin:change_parameters_retry',
                            kwargs={'id': database.id})
                )
        else:
            self.form_status = self.EDITABLE
            can_do_change_parameters, error = (
                database.can_do_change_parameters()
            )
            if not can_do_change_parameters:
                messages.add_message(request, messages.ERROR, error)
                return self.get(request)
            else:
                changed_parameters, error = self.update_database_parameters(
                    request.POST, database
                )
                if error:
                    messages.add_message(request, messages.ERROR, error)
                    return self.get(request)
                if changed_parameters:
                    return HttpResponseRedirect(
                        reverse('admin:change_parameters',
                                kwargs={'id': database.id})
                    )
                return self.get(request)

    @database_view_class('parameters')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        self.there_is_static_parameter = False
        self.form_status = self.PROTECTED
        return super(DatabaseParameters, self).dispatch(
            request, *args, **kwargs
        )


@database_view("")
def database_change_parameters(request, context, database):
    can_do_change_parameters, error = database.can_do_change_parameters()
    if not can_do_change_parameters:
        messages.add_message(request, messages.ERROR, error)
    else:
        TaskRegister.database_change_parameters(
            database=database,
            user=request.user
        )

    return HttpResponseRedirect(
        reverse(
            'admin:logical_database_parameters', kwargs={'id': database.id}
        )
    )


@database_view("")
def database_change_parameters_retry(request, context, database):
    can_do_change_parameters, error = database.can_do_change_parameters_retry()
    if can_do_change_parameters:
        changed_parameters, parameter_error = (
            DatabaseParameters.update_database_parameters(
                request.POST, database
            )
        )

        if parameter_error:
            messages.add_message(request, messages.ERROR, error)
            return HttpResponseRedirect(
                reverse('admin:change_parameters_retry',
                        kwargs={'id': database.id})
            )

        last_change_parameters = database.change_parameters.last()

        if not last_change_parameters.is_status_error:
            error = ("Cannot do retry, last change parameters status is"
                     " '{}'!").format(
                last_change_parameters.get_status_display()
            )
        else:
            since_step = last_change_parameters.current_step

    if error:
        messages.add_message(request, messages.ERROR, error)
    else:
        TaskRegister.database_change_parameters(
            database=database,
            user=request.user,
            since_step=since_step
        )

    return HttpResponseRedirect(
        reverse(
            'admin:logical_database_parameters', kwargs={'id': database.id}
        )
    )


@database_view('metrics')
def database_metrics(request, context, database):
    context['hostname'] = request.GET.get(
        'hostname',
        database.infra.instances.first().hostname.hostname.split('.')[0]
    )

    context['source'] = request.GET.get('source', 'zabbix')

    if context['source'] == 'sofia':
        context['second_source'] = 'zabbix'
    else:
        context['second_source'] = 'sofia'

    user = request.user
    if len(user.team_set.filter(organization__external=False)) > 0:
        context['can_show_sofia_metrics'] = True
    else:
        context['can_show_sofia_metrics'] = False

    context['hosts'] = []
    for host in Host.objects.filter(
            instances__databaseinfra=database.infra).distinct():
        context['hosts'].append(host.hostname.split('.')[0])

    credential = get_credentials_for(
        environment=database.databaseinfra.environment,
        credential_type=CredentialType.GRAFANA
    )
    instance = database.infra.instances.filter(
        hostname__hostname__contains=context['hostname']
    ).first()

    organization = database.team.organization
    if organization and organization.external:
        endpoint = organization.grafana_endpoint
        datasource = organization.grafana_datasource
    else:
        endpoint = credential.endpoint
        datasource = credential.get_parameter_by_name('environment')

    engine_type = (
        database.engine_type if not database.engine_type == "mysql_percona" else "mysql"
    )

    grafana_url_zabbix = '{}/dashboard/{}?{}={}&{}={}&{}={}&{}={}'.format(
        endpoint,
        credential.project.format(engine_type),
        credential.get_parameter_by_name('db_param'), instance.dns,
        credential.get_parameter_by_name('os_param'),
        instance.hostname.hostname,
        credential.get_parameter_by_name('disk_param'),
        credential.get_parameter_by_name('disk_dir'),
        credential.get_parameter_by_name('env_param'),
        datasource
    )

    if organization and organization.external:
        grafana_url_zabbix += "&orgId={}".format(organization.grafana_orgid)

    context['grafana_url_zabbix'] = grafana_url_zabbix

    print "grafana_url_zabbix:{}", grafana_url_zabbix

    dashboard = credential.get_parameter_by_name('sofia_dbaas_database_dashboard')

    dashboard = dashboard.format(engine_type)
    url = "{}/{}?var-host_name={}&var-datasource={}".format(
        credential.endpoint,
        dashboard,
        instance.hostname.hostname.split('.')[0],
        credential.get_parameter_by_name('datasource'),
        )

    context['grafana_url_sofia'] = url

    return render_to_response(
        "logical/database/details/metrics_tab.html",
        context, RequestContext(request)
    )


def _disk_resize(request, database):
    try:
        check_is_database_enabled(database.id, 'disk resize')
    except DisabledDatabase as err:
        messages.add_message(request, messages.ERROR, err.message)
        return

    disk_offering = DiskOffering.objects.get(
        id=request.POST.get('disk_offering')
    )

    current_used = round(database.used_size_in_gb, 2)
    offering_size = round(disk_offering.size_gb(), 2)
    if current_used >= offering_size:
        messages.add_message(
            request, messages.ERROR,
            'Your database has {} GB, please choose a bigger disk'.format(
                current_used
            )
        )
        return

    Database.disk_resize(
        database=database,
        new_disk_offering=disk_offering.id,
        user=request.user
    )


def _vm_resize(request, database):
    try:
        check_is_database_dead(database.id, 'VM resize')
        check_is_database_enabled(database.id, 'VM resize')
    except DisabledDatabase as err:
        messages.add_message(request, messages.ERROR, err.message)
    else:
        offering = Offering.objects.get(
            id=request.POST.get('vm_offering')
        )
        Database.resize(
            database=database,
            offering=offering,
            user=request.user,
        )


def get_last_valid_resize(request, database):
    can_do_resize, error = database.can_do_resize_retry()
    if not can_do_resize:
        messages.add_message(request, messages.ERROR, error)
        return None

    last_resize = database.resizes.last()
    if not last_resize.is_status_error:
        error = "Cannot do retry, last resize status is '{}'!".format(
            last_resize.get_status_display()
        )
        messages.add_message(request, messages.ERROR, error)
        return None

    return last_resize


@database_view("")
def database_resize_retry(request, context, database):
    last_resize = get_last_valid_resize(request, database)
    if last_resize:
        TaskRegister.database_resize_retry(
            database=database,
            user=request.user,
            offering=last_resize.target_offer,
            original_offering=last_resize.source_offer,
            since_step=last_resize.current_step
        )

    return HttpResponseRedirect(
        reverse('admin:logical_database_resizes', kwargs={'id': database.id})
    )


@database_view("")
def database_resize_rollback(request, context, database):
    last_resize = get_last_valid_resize(request, database)
    if last_resize:
        TaskRegister.database_resize_rollback(last_resize, request.user)

    return HttpResponseRedirect(
        reverse('admin:logical_database_resizes', kwargs={'id': database.id})
    )


@database_view("")
def database_upgrade(request, context, database):
    can_do_upgrade, error = database.can_do_upgrade()
    if not can_do_upgrade:
        messages.add_message(request, messages.ERROR, error)
    else:

        TaskRegister.database_upgrade(
            database=database,
            user=request.user
        )
    return HttpResponseRedirect(
        reverse(
            'admin:logical_database_upgrade', kwargs={'id': database.id}
        )
    )


@database_view("")
def database_upgrade_retry(request, context, database):
    can_do_upgrade, error = database.can_do_upgrade_retry()
    if can_do_upgrade:
        source_plan = database.databaseinfra.plan
        upgrades = database.upgrades.filter(source_plan=source_plan)
        last_upgrade = upgrades.last()
        if not last_upgrade:
            error = "Database does not have upgrades from {} {}!".format(
                source_plan.engine.engine_type, source_plan.engine.version
            )
        elif not last_upgrade.is_status_error:
            error = "Cannot do retry, last upgrade status is '{}'!".format(
                last_upgrade.get_status_display()
            )
        else:
            since_step = last_upgrade.current_step

    if error:
        messages.add_message(request, messages.ERROR, error)
    else:

        TaskRegister.database_upgrade(
            database=database,
            user=request.user,
            since_step=since_step
        )
    return HttpResponseRedirect(
        reverse(
            'admin:logical_database_upgrade', kwargs={'id': database.id}
        )
    )


def _upgrade_patch(request, database, target_patch):
    can_do_upgrade, error = database.can_do_upgrade_patch()

    if not can_do_upgrade:
        messages.add_message(request, messages.ERROR, error)
    else:
        target_patch = database.engine.available_patches(
            database
        ).get(
            id=target_patch
        )

        TaskRegister.database_upgrade_patch(
            database=database,
            patch=target_patch,
            user=request.user
        )


@database_view("")
def database_upgrade_patch_retry(request, context, database):
    _upgrade_patch_retry(request, database)
    return HttpResponseRedirect(
        reverse('admin:logical_database_resizes', kwargs={'id': database.id})
    )


def _upgrade_patch_retry(request, database):
    can_do_upgrade, error = database.can_do_upgrade_patch_retry()
    if can_do_upgrade:
        upgrades = database.upgrades_patch.all()
        last_upgrade = upgrades.last()
        if not last_upgrade:
            error = "Database does not have upgrades"
        elif not last_upgrade.is_status_error:
            error = "Cannot do retry, last upgrade status is '{}'!".format(
                last_upgrade.get_status_display()
            )
        else:
            since_step = last_upgrade.current_step

    if error:
        messages.add_message(request, messages.ERROR, error)
    else:

        TaskRegister.database_upgrade_patch(
            database=database,
            patch=last_upgrade.target_patch,
            user=request.user,
            since_step=since_step
        )


@database_view('resizes')
def database_resizes(request, context, database):
    if request.method == 'POST':
        if 'disk_resize' in request.POST and request.POST.get('disk_offering'):
            _disk_resize(request, database)
        elif (request.POST.get('resize_vm_yes') == 'yes' and request.POST.get(
                'vm_offering'
             )):
            _vm_resize(request, database)
        else:
            disk_auto_resize = request.POST.get('disk_auto_resize', False)
            database.disk_auto_resize = disk_auto_resize
            database.save()

    context['last_vm_resize'] = database.resizes.last()
    context['vm_offerings'] = list(database.environment.offerings.all(
    ).order_by('cpus', 'memory_size_mb'))
    context['current_vm_offering'] = database.infra.hosts[0].offering
    for offering in context['vm_offerings']:
        if offering == context['current_vm_offering']:
            break
    else:
        context['vm_offerings'].append(context['current_vm_offering'])

    disk_used_size_kb = database.infra.disk_used_size_in_kb
    if not disk_used_size_kb:
        disk_used_size_kb = database.used_size_in_kb
    context['disk_offerings'] = list(
        DiskOffering.objects.filter(size_kb__gt=disk_used_size_kb)
    )
    if database.infra.disk_offering not in context['disk_offerings']:
        context['disk_offerings'].insert(0, database.infra.disk_offering)

    return render_to_response(
        "logical/database/details/resizes_tab.html",
        context, RequestContext(request)
    )


class DatabaseMigrateEngineRetry(View):

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(
            reverse(
                'admin:logical_database_maintenance',
                kwargs={'id': self.database.id}
            )
        )

    @database_view_class('')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        return super(DatabaseMigrateEngineRetry, self).dispatch(
            request, *args, **kwargs
        )


class DatabaseMaintenanceView(TemplateView):
    template_name = "logical/database/details/maintenance_tab.html"
    WEEKDAYS = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday')
    ]

    def get_object(self, schedule_id):
        return TaskSchedule.objects.get(id=schedule_id)

    def has_maintenance_backup_changed(self, parameters):
        return any(key in self.request.POST for key in parameters)

    def _update_schedule_tasks_for_next_maintenance_window(self, *args, **kw):
        payload = self.request.POST

        for pos, scheduled_id in enumerate(payload.getlist('scheduled_id')):
            task = self.get_object(schedule_id)
            task.scheduled_for = TaskSchedule.next_maintenance_window(
                datetime.date.today(),
                int(payload.get('maintenance_window')),
                int(payload.get('maintenance_day')),
            )
            is_valid, err_msg = task.is_valid()
            if not is_valid:
                return is_valid, err_msg
            task.save()
            task.send_mail()

        return True, ''

    def _change_schedule_maintenance(self):
        payload = self.request.POST
        task_id_for_change = payload.get('changed_schedule')
        task = self.get_object(task_id_for_change)
        task_date = payload.get('scheduled_for_date')
        task_time = payload.get('scheduled_for_time')
        task.scheduled_for = datetime.datetime.strptime(
            "{} {}".format(task_date, task_time),
            "%Y-%m-%d %H:%M:%S"
        )
        is_valid, err_msg = task.is_valid()
        if not is_valid:
            return is_valid, err_msg
        task.save()
        task.send_mail()

        return True, ''

    def _update_schedule_task(self):
        payload = self.request.POST
        maintenance_changed = payload.get('maintenance_changed')
        user_want_update = payload.get('_save') == 'save_and_update_task'
        user_changed_schedule = payload.get('schedule_maintenance') == '_save'
        if maintenance_changed and user_want_update:
            return self._update_schedule_tasks_for_next_maintenance_window()
        elif user_changed_schedule:
            return self._change_schedule_maintenance()

        return True, ''

    def post(self, request, *args, **kwargs):
        is_valid, err_msg = self._update_schedule_task()
        if not is_valid:
            messages.add_message(
                request,
                messages.ERROR,
                err_msg
            )
            self.context['err_msg'] = err_msg
            return self.render_to_response(self.get_context_data())
        if self.has_maintenance_backup_changed([
            'maintenance_window',
            'maintenance_day'
        ]):
            maintenance_window = request.POST.get('maintenance_window')
            maintenance_day = request.POST['maintenance_day']
            self.database.infra.maintenance_window = maintenance_window
            self.database.infra.maintenance_day = maintenance_day
            self.database.infra.save()
        else:
            self.database.save()

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        self.context['tasks_scheduled'] = TaskSchedule.objects.filter(
            database=self.database,
            status=TaskSchedule.SCHEDULED
        ).order_by('-scheduled_for')

        self.context['tasks_executed'] = TaskSchedule.objects.filter(
            database=self.database,
        ).exclude(status=TaskSchedule.SCHEDULED).order_by('-finished_at')

        # Maintenance region
        self.context['maintenance_windows'] = (
            DatabaseForm.MAINTENANCE_WINDOW_CHOICES
        )
        self.context['current_maintenance_window'] = int(
            self.database.infra.maintenance_window
        )
        self.context['maintenance_days'] = DatabaseMaintenanceView.WEEKDAYS
        self.context['current_maintenance_day'] = int(
            self.database.infra.maintenance_day
        )

        self.context['tasks_scheduled'] = TaskSchedule.objects.filter(
            database=self.database,
            status=TaskSchedule.SCHEDULED
        )

        return self.context

    @database_view_class('maintenance')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        return super(DatabaseMaintenanceView, self).dispatch(
            request, *args, **kwargs
        )


class DatabaseUpgradeView(TemplateView):
    template_name = "logical/database/details/upgrade_tab.html"

    def is_upgrade_patch(self):
        return ('upgrade_patch' in self.request.POST and
                self.request.POST.get('target_patch'))

    def is_upgrade_patch_retry(self):
        return 'upgrade_patch_retry' in self.request.POST

    def is_engine_migration(self):
        return 'migrate_plan' in self.request.POST

    def is_engine_migration_retry(self):
        return 'migrate_plan_retry' in self.request.POST

    def is_upgrade(self):
        return 'upgrade_database' in self.request.POST

    def is_upgrade_retry(self):
        return 'upgrade_database_retry' in self.request.POST

    def get_or_none_retry_migrate_engine_plan(self):
        engine_migration = DatabaseMigrateEngine.objects.need_retry(
            database=self.database
        )

        if engine_migration:
            return engine_migration.target_plan

        return None

    def post(self, request, *args, **kwargs):
        if self.is_upgrade_patch():
            _upgrade_patch(
                request,
                self.database,
                request.POST.get('target_patch')
            )
        elif self.is_upgrade_patch_retry():
            _upgrade_patch_retry(request, self.database)
        elif self.is_engine_migration():
            target_plan_id = self.database.infra.plan.migrate_engine_equivalent_plan.pk
            self.migrate_engine(target_plan_id)
        elif self.is_engine_migration_retry():
            self.retry_migrate_engine()
        elif self.is_upgrade():
            self.upgrade_database(request)
        elif self.is_upgrade_retry():
            self.upgrade_database(request, retry=True)

        return self.render_to_response(self.get_context_data())

    def upgrade_database(self, request, retry=False):
        try:
            service_obj = services.UpgradeDatabaseService(
                request, self.database, retry=retry, rollback=False
            )
            service_obj.execute()
        except (
            exceptions.DatabaseNotAvailable, exceptions.ManagerInvalidStatus,
            exceptions.ManagerNotFound, exceptions.DatabaseUpgradePlanNotFound
        ) as error:
            messages.add_message(self.request, messages.ERROR, str(error))

    def has_update_mongodb_30(self):
        return (
            self.database.is_mongodb_24() and
            self.request.user.has_perm(constants.PERM_UPGRADE_MONGO24_TO_30)
        )

    def can_do_upgrade(self):
        return (
            bool(self.database.infra.plan.engine_equivalent_plan) and
            self.request.user.has_perm(constants.PERM_UPGRADE_DATABASE)
        )

    def retry_migrate_engine(self):
        error = None
        last_migration = DatabaseMigrateEngine.objects.filter(
            database=self.database
        ).last()

        if not last_migration:
            error = "Database does not have engine migrations"
        elif not last_migration.is_status_error:
            error = ("Cannot do retry, last engine migration. "
                     "Status is '{}'!").format(
                        last_upgrade.get_status_display())
        else:
            since_step = last_migration.current_step

        if error:
            messages.add_message(self.request, messages.ERROR, error)
        else:
            self.migrate_engine(last_migration.target_plan.pk, since_step)

    def migrate_engine(self, target_migrate_plan_id, since_step=None):
        retry = False

        if since_step:
            retry = True

        can_do_engine_migration, error = self.database.can_do_engine_migration(
            retry=retry
        )

        if not can_do_engine_migration:
            messages.add_message(self.request, messages.ERROR, error)
        else:
            target_migrate_plan = Plan.objects.filter(
                pk=target_migrate_plan_id
            ).first()

            TaskRegister.engine_migrate(
                database=self.database,
                target_plan=target_migrate_plan,
                user=self.request.user,
                since_step=since_step
            )

    def required_disk_available_patches(self, patches):
        patches_required_disk_size = []
        for patch in patches:
            required_disk_size_gb = patch.required_disk_size_gb
            if self.database.infra.check_rfs_size(required_disk_size_gb):
                patches_required_disk_size.append(patch)
        return patches_required_disk_size


    def get_context_data(self, **kwargs):
        # Upgrade region
        self.context['upgrade_mongo_24_to_30'] = self.has_update_mongodb_30()
        self.context['can_do_upgrade'] = self.can_do_upgrade()
        self.context['last_upgrade'] = self.database.upgrades.filter(
            source_plan=self.database.infra.plan
        ).last()

        # Patch region
        available_patches = self.database.engine.available_patches(
            self.database
        ).all()
        patches_required_disk_size = self.required_disk_available_patches(
            available_patches
        )

        self.context['retry_patch'] = DatabaseUpgradePatch.objects.need_retry(
            database=self.database
        )
        self.context['all_patches_blocked_by_disk'] = (
            available_patches and not patches_required_disk_size
        )

        self.context['has_patches_blocked_by_disk'] = (
            list(available_patches) != list(patches_required_disk_size)
        )

        if patches_required_disk_size:
            available_patches = patches_required_disk_size

        self.context['available_patches'] = (
            available_patches
        )

        # Plan migration region
        self.context['available_plans_for_migration'] = (
            self.database.plan.available_plans_for_migration
        )

        self.context['retry_migrate_plan'] = (
            self.get_or_none_retry_migrate_engine_plan()
        )

        can_upgrade_db = (
            self.database.databaseinfra.plan.replication_topology.can_upgrade_db  # noqa
        )
        self.context['has_any_upgrade_available'] = any([
            self.context['retry_migrate_plan'],
            self.context['available_plans_for_migration'],
            self.context['available_patches'],
            self.context['upgrade_mongo_24_to_30'] and can_upgrade_db,
            self.context['can_do_upgrade'] and can_upgrade_db,
        ])

        return self.context

    @database_view_class('upgrade')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        return super(DatabaseUpgradeView, self).dispatch(
            request, *args, **kwargs
        )


class UpgradeDatabaseRetryView(View):

    def get(self, request, *args, **kwargs):
        try:
            service_obj = services.UpgradeDatabaseService(
                request, self.database, retry=True
            )
            service_obj.execute()
        except (
            exceptions.DatabaseNotAvailable, exceptions.ManagerInvalidStatus,
            exceptions.ManagerNotFound, exceptions.DatabaseUpgradePlanNotFound
        ) as error:
            messages.add_message(self.request, messages.ERROR, str(error))

        return HttpResponseRedirect(
            reverse(
                'admin:logical_database_upgrade',
                kwargs={'id': self.database.id}
            )
        )

    @database_view_class('')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        return super(UpgradeDatabaseRetryView, self).dispatch(
            request, *args, **kwargs
        )


class AddInstancesDatabaseRetryView(View):

    def get(self, request, *args, **kwargs):
        service_obj = services.AddReadOnlyInstanceService(
            request, self.database, retry=True
        )
        service_obj.execute()
        return HttpResponseRedirect(
            reverse(
                'admin:logical_database_hosts',
                kwargs={'id': self.database.id}
            )
        )

    @database_view_class('')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        return super(AddInstancesDatabaseRetryView, self).dispatch(
            request, *args, **kwargs
        )


class AddInstancesDatabaseRollbackView(View):

    def get(self, request, *args, **kwargs):
        service_obj = services.AddReadOnlyInstanceService(
            request, self.database, rollback=True
        )
        service_obj.rollback()
        return HttpResponseRedirect(
            reverse(
                'admin:logical_database_hosts',
                kwargs={'id': self.database.id}
            )
        )

    @database_view_class('')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        return super(AddInstancesDatabaseRollbackView, self).dispatch(
            request, *args, **kwargs
        )


class DatabaseHostsView(TemplateView):
    template_name = "logical/database/details/hosts_tab.html"

    def is_add_read_only(self):
        return 'add_read_only' in self.request.POST

    def is_add_read_only_retry(self):
        return 'add_read_only_retry' in self.request.POST

    def is_add_read_only_rollback(self):
        return 'add_read_only_rollback' in self.request.POST

    def is_recreate_slave(self):
        return 'recreate_slave' in self.request.POST

    def post(self, request, *args, **kwargs):
        if self.is_add_read_only():
            self.add_instace_to_database(request)
        elif self.is_add_read_only_retry():
            self.add_instace_to_database(request, retry=True)
        elif self.is_add_read_only_rollback():
            self.add_instace_to_database(request, rollback=True)
        elif self.is_recreate_slave():
            host_id = request.POST.get('host_id')
            host = self.database.infra.instances.filter(
                hostname__id=host_id
            ).first().hostname
            TaskRegister.recreate_slave(host, request.user)
            return HttpResponseRedirect(
                reverse(
                    'admin:logical_database_hosts',
                    kwargs={'id': self.database.id}
                )
            )
        return self.render_to_response(self.get_context_data())

    def add_instace_to_database(self, request, retry=False, rollback=False):
        try:
            service_obj = services.AddReadOnlyInstanceService(
                request, self.database, retry=retry, rollback=rollback
            )

            if rollback:
                service_obj.rollback()
            else:
                service_obj.execute()
        except (
            exceptions.DatabaseIsNotHA, exceptions.DatabaseNotAvailable,
            exceptions.ManagerInvalidStatus, exceptions.ManagerNotFound,
            exceptions.ReadOnlyHostsLimit, exceptions.RequiredNumberOfInstances
        ) as error:
            messages.add_message(self.request, messages.ERROR, str(error))

    def get_context_data(self, **kwargs):
        hosts = OrderedDict()
        instances = self.database.infra.instances.all().order_by('shard', 'id')
        if instances[0].shard:
            instances_tmp = []
            instances_slaves = []
            last_shard = None
            for instance in instances:
                if instance.is_current_write:
                    instances_tmp.append(instance)
                    last_shard = instance.shard
                    if instances_slaves:
                        instances_tmp += instances_slaves
                        instances_slaves = []
                else:
                    if last_shard == instance.shard:
                        instances_tmp.append(instance)
                    else:
                        instances_slaves.append(instance)
            if instances_slaves:
                instances_tmp += instances_slaves
                instances_slaves = []

            instances = instances_tmp

        for instance in instances:
            if instance.hostname not in hosts:
                hosts[instance.hostname] = []
            hosts[instance.hostname].append(instance)

        self.context['core_attribute'] = self.database.engine.write_node_description
        self.context['read_only_attribute'] = self.database.engine.read_node_description
        self.context['last_reinstall_vm'] = self.database.reinstall_vm.last()
        self.context['last_recreat_slave'] = RecreateSlave.objects.filter(
            host__in=self.database.infra.hosts,
            can_do_retry=True,
            status=RecreateSlave.ERROR
        ).last()
        self.context['instances_core'] = []
        self.context['instances_read_only'] = []
        for host, instances in hosts.items():
            attributes = []
            is_read_only = False
            status = ''
            switch_database = False
            for instance in instances:
                is_read_only = instance.read_only
                status = instance.status_html()

                if not instance.is_database:
                    self.context['non_database_attribute'] = (
                        instance.get_instance_type_display()
                    )
                    attributes.append(self.context['non_database_attribute'])
                elif instance.is_current_write:
                    attributes.append(self.context['core_attribute'])
                    if self.database.databaseinfra.plan.is_ha:
                        switch_database = True
                else:
                    attributes.append(self.context['read_only_attribute'])

            full_description = host.hostname

            padding = False
            if not instance.is_current_write:
                if instance.shard:
                    padding = True

            if len(hosts) > 1:
                full_description += ' - ' + '/'.join(attributes)

            host_data = {
                'id': host.id, 'status': status, 'description': full_description,
                'switch_database': switch_database, 'padding': padding,
                'is_database': host.is_database
            }

            if is_read_only:
                self.context['instances_read_only'].append(host_data)
            else:
                self.context['instances_core'].append(host_data)

        self.context['max_read_hosts'] = Configuration.get_by_name_as_int(
            'max_read_hosts', 5
        )
        enable_host = self.context['max_read_hosts'] - len(
            self.context['instances_read_only']
        )
        self.context['enable_host'] = range(1, enable_host+1)
        self.context['add_read_only_retry'] = (
            AddInstancesToDatabase.objects.need_retry(
                database=self.database
            )
        )

        return self.context

    @database_view_class('hosts')
    def dispatch(self, request, *args, **kwargs):
        self.context, self.database = args
        return super(DatabaseHostsView, self).dispatch(
            request, *args, **kwargs
        )


def database_delete_host(request, database_id, host_id):
    database = Database.objects.get(id=database_id)
    instance = database.infra.instances.get(hostname_id=host_id)

    can_delete = True
    if not instance.read_only:
        messages.add_message(
            request, messages.ERROR,
            'Host is not read only, cannot be removed.'
        )
        can_delete = False

    if database.is_being_used_elsewhere():
        messages.add_message(
            request, messages.ERROR,
            ('Host cannot be deleted because database is in use by '
             'another task.')
        )
        can_delete = False

    if can_delete:
        TaskRegister.database_remove_instance(
            database=database, instance=instance, user=request.user
        )

    return HttpResponseRedirect(
        reverse('admin:logical_database_hosts', kwargs={'id': database.id})
    )


def _clone_database(request, database):
    can_be_cloned, error = database.can_be_cloned()
    if error:
        messages.add_message(request, messages.ERROR, error)
        return

    if 'clone_name' not in request.POST:
        messages.add_message(
            request, messages.ERROR, 'Destination is required'
        )
        return

    if 'clone_env' not in request.POST:
        messages.add_message(
            request, messages.ERROR, 'Environment is required'
        )
        return

    if 'clone_plan' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Plan is required')
        return

    name = request.POST['clone_name']
    environment = Environment.objects.get(id=request.POST['clone_env'])
    plan = Plan.objects.get(id=request.POST['clone_plan'])

    current = len(database.team.databases_in_use_for(environment))
    if current >= database.team.database_alocation_limit:
        messages.add_message(
            request, messages.ERROR,
            'The database allocation limit of %s has been exceeded for the '
            'team: {} => {}'.format(
                current, database.team.database_alocation_limit
            )
        )
        return

    if name in database.infra.get_driver().RESERVED_DATABASES_NAME:
        messages.add_message(
            request, messages.ERROR,
            '{} is a reserved database name'.format(name)
        )
        return

    if len(name) > 40:
        messages.add_message(request, messages.ERROR, 'Database name too long')
        return

    if Database.objects.filter(name=name, environment=environment):
        messages.add_message(
            request, messages.ERROR,
            'There is already a database called {} on {}'.format(
                name, environment
            )
        )
        return

    Database.clone(
        database=database, clone_name=name, plan=plan,
        environment=environment, user=request.user
    )


def _restore_database(request, database):
    can_be_restored, error = database.can_be_restored()
    if error:
        messages.add_message(request, messages.ERROR, error)
        return

    if 'restore_snapshot' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Snapshot is required')
        return

    snapshot = request.POST.get('restore_snapshot')
    Database.restore(database=database, snapshot=snapshot, user=request.user)


def _delete_snapshot(request, database):
    if 'restore_snapshot' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Snapshot is required')
        return

    snapshot_id = request.POST.get('restore_snapshot')
    for instance in database.infra.instances.all():
        snapshot = instance.backup_instance.filter(id=snapshot_id).first()
        if snapshot:
            break
    else:
        messages.add_message(
            request, messages.ERROR, 'The snapshot {} is not from {}'.format(
                snapshot_id, database
            )
        )
        return

    if snapshot.purge_at:
        messages.add_message(
            request, messages.ERROR,
            'This snapshot, was deleted at {}'.format(snapshot.purge_at)
        )
        return
    elif snapshot.is_automatic:
        messages.add_message(
            request, messages.ERROR,
            'This is an automatic snapshot, it could not be deleted'
        )
        return

    TaskRegister.database_remove_backup(
        database=database, snapshot=snapshot, user=request.user.username
    )


@database_view("")
def database_make_backup(request, context, database):
    error = None
    try:
        check_is_database_dead(database.id, 'Backup')
        check_is_database_enabled(database.id, 'Backup')
    except DisabledDatabase as err:
        error = err.message

    if not context['is_dba']:
        error = "Only DBA's can do database backup"

    if error:
        messages.add_message(request, messages.ERROR, error)
    else:
        TaskRegister.database_backup(
            database=database, user=request.user.username
        )

    return HttpResponseRedirect(
        reverse('admin:logical_database_backup', kwargs={'id': database.id})
    )


@database_view('backup')
def database_backup(request, context, database):
    if request.method == 'POST':
        backup_hour = int(request.POST.get('backup_hour', 0))
        maintenance_window = database.infra.maintenance_window
        if backup_hour == maintenance_window:
            messages.add_message(
                request,
                messages.ERROR,
                'Backup hour must not be equal then maintenance window.'
            )
        else:
            database.infra.backup_hour = backup_hour
            database.infra.save()
        if 'database_clone' in request.POST:
            _clone_database(request, database)
        elif 'database_restore' in request.POST:
            _restore_database(request, database)
        elif 'snapshot_delete' in request.POST:
            _delete_snapshot(request, database)
        elif 'backup_path' in request.POST:
            database.backup_path = request.POST['backup_path']
            database.save()

    groups = []
    context['snapshots'] = []
    for instance in database.infra.instances.all():
        for backup in instance.backup_instance.filter(purge_at=None):

            group = backup.group
            if group and group in groups:
                continue

            groups.append(group)
            context['snapshots'].append(backup)

    context['snapshots'] = context['snapshots']
    context['environments'] = Environment.objects.all()
    context['plans'] = Plan.objects.filter(
        engine=database.engine, is_active=True,
    )
    # Backup region
    context['backup_hours'] = DatabaseForm.BACKUP_HOUR_CHOICES
    context['current_backup_hour'] = int(
        database.infra.backup_hour
    )

    return render_to_response(
        "logical/database/details/backup_tab.html",
        context, RequestContext(request)
    )


@database_view('dns')
def database_dns(request, context, database):
    context['can_remove_extra_dns'] = request.user.has_perm(
        'extra_dns.delete_extradns'
    )
    context['can_add_extra_dns'] = request.user.has_perm(
        'extra_dns.add_extradns'
    )

    return render_to_response(
        "logical/database/details/dns_tab.html",
        context, RequestContext(request)
    )


def _destroy_databases(request, database):
    can_be_deleted, error = database.can_be_deleted()
    if error:
        messages.add_message(request, messages.ERROR, error)
        return

    if 'database_name' not in request.POST:
        messages.add_message(
            request, messages.ERROR, 'Database name is required'
        )
        return

    if request.POST['database_name'] != database.name:
        messages.add_message(
            request, messages.ERROR, 'Database name is not equal'
        )
        return

    in_quarantine = database.is_in_quarantine
    database.destroy(request.user)
    if not in_quarantine:
        return HttpResponseRedirect(
            reverse('admin:logical_database_changelist')
        )

    return HttpResponseRedirect(
        '{}?user={}'.format(
            reverse('admin:notification_taskhistory_changelist'),
            request.user.username
        )
    )


@database_view('destroy')
def database_destroy(request, context, database):
    if request.method == 'POST':
        if 'database_destroy' in request.POST:
            response = _destroy_databases(request, database)
            if response:
                return response
        if 'undo_quarantine' in request.POST and database.is_in_quarantine:
            database.is_in_quarantine = False
            database.save()

    return render_to_response(
        "logical/database/details/destroy_tab.html",
        context, RequestContext(request)
    )


def database_switch_write(request, database_id, host_id):
    database = Database.objects.get(id=database_id)
    instances = database.infra.instances.filter(hostname_id=host_id)
    for instance in instances:
        if instance.is_database:
            break

    can_switch = True

    if database.is_being_used_elsewhere():
        messages.add_message(
            request, messages.ERROR,
            ('Can not switch write database because it is in use by '
             'another task.')
        )
        can_switch = False

    if can_switch:
        TaskRegister.database_switch_write(
            database=database, user=request.user, instance=instance
        )

    return HttpResponseRedirect(
        reverse('admin:logical_database_hosts', kwargs={'id': database.id})
    )


def database_reinstall_vm(request, database_id, host_id):
    database = Database.objects.get(id=database_id)
    instances = database.infra.instances.filter(hostname_id=host_id)
    for instance in instances:
        if instance.is_database:
            break

    can_reinstall_vm = True

    if database.is_being_used_elsewhere():
        messages.add_message(
            request, messages.ERROR,
            'Can not reinstall VM because database is in use by another task.'
        )
        can_reinstall_vm = False

    if can_reinstall_vm:
        TaskRegister.database_reinstall_vm(
            instance=instance,
            user=request.user,
        )

    return HttpResponseRedirect(
        reverse('admin:logical_database_hosts', kwargs={'id': database.id})
    )


@database_view("")
def database_reinstall_vm_retry(request, context, database):
    last_reinstall_vm = database.reinstall_vm.last()
    can_reinstall_vm = True

    if not last_reinstall_vm:
        messages.add_message(
            request, messages.ERROR,
            ('Can not retry reinstall VM because there is not any reinstall '
             'task in progress.')
        )
        can_reinstall_vm = False

    elif database.is_being_used_elsewhere(
            ['notification.tasks.reinstall_vm_database']):
        messages.add_message(
            request, messages.ERROR,
            ('Can not retry reinstall VM because database is in use by '
             'another task.')
        )
        can_reinstall_vm = False

    else:
        instance = last_reinstall_vm.instance
        since_step = last_reinstall_vm.current_step

    if can_reinstall_vm:
        TaskRegister.database_reinstall_vm(
            instance=instance,
            user=request.user,
            since_step=since_step,
        )

    return HttpResponseRedirect(
        reverse('admin:logical_database_hosts', kwargs={'id': database.id})
    )


@database_view('migrate')
def database_migrate(request, context, database):
    if not database.is_host_migrate_available:
        messages.add_message(
            request, messages.ERROR, "This database cannot be migrated"
        )
        return database_details(request, database.id)

    environment = database.infra.environment
    if request.POST:
        can_migrate, error = database.can_migrate_host()
        if not can_migrate:
            messages.add_message(request, messages.ERROR, error)
        elif 'host_id' in request.POST:
            host = get_object_or_404(Host, pk=request.POST.get('host_id'))
            zone = request.POST["new_zone"]
            TaskRegister.host_migrate(host, zone, environment, request.user)
        elif 'new_environment' in request.POST:
            environment = get_object_or_404(
                Environment, pk=request.POST.get('new_environment')
            )
            offering = get_object_or_404(
                Offering, pk=request.POST.get('new_offering')
            )
            if environment not in offering.environments.all():
                messages.add_message(
                    request, messages.ERROR,
                    "There is no offering {} to {} environment".format(
                        offering, environment
                    )
                )
                return

            hosts_zones = OrderedDict()
            data = json.loads(request.POST.get('hosts_zones'))
            for host_id, zone in data.items():
                host = get_object_or_404(Host, pk=host_id)
                hosts_zones[host] = zone
            if not hosts_zones:
                messages.add_message(
                    request, messages.ERROR, "There is no host to migrate"
                )
            else:
                TaskRegister.database_migrate(
                    database, environment, offering, request.user, hosts_zones
                )
        return

    hosts = set()
    zones = set()
    instances = database.infra.instances.all().order_by('shard', 'id')
    for instance in instances:
        host = instance.hostname
        if host in hosts:
            continue

        hp = Provider(instance, environment)
        try:
            host_info = hp.host_info(host)
        except Exception as e:
            LOG.error("Could get host info {} - {}".format(host, e))
        else:
            host.current_zone = host_info['zone']
        hosts.add(host)
    context['hosts'] = sorted(hosts, key=lambda host: host.hostname)
    context['zones'] = sorted(zones)

    context["environments"] = set()
    for group in environment.groups.all():
        for env in group.environments.all():
            context["environments"].add(env)
    context["current_environment"] = environment
    context["current_offering"] = database.infra.offering

    from maintenance.models import HostMigrate
    migrates = HostMigrate.objects.filter(host__in=hosts)
    context["last_host_migrate"] = migrates.last()
    return render_to_response(
        "logical/database/details/migrate_tab.html", context,
        RequestContext(request)
    )


def zones_for_environment(request, database_id, environment_id):
    database = get_object_or_404(Database, pk=database_id)
    environment = get_object_or_404(Environment, pk=environment_id)
    hp = Provider(database.infra.instances.first(), environment)
    zones = sorted(hp.list_zones())
    return HttpResponse(
        json.dumps({"zones": zones}), content_type="application/json"
    )


class ExecuteScheduleTaskView(RedirectView):
    pattern_name = 'admin:logical_database_maintenance'

    def get_object(self):
        return TaskSchedule.objects.get(id=self.kwargs['task_id'])

    def get(self, *args, **kw):
        execute_scheduled_maintenance.delay(
            task=self.get_object(),
            user=self.request.user,
            auto_rollback=False
        )
        self.kwargs.pop('task_id')
        return super(ExecuteScheduleTaskView, self).get(*args, **self.kwargs)
