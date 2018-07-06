# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
from collections import OrderedDict
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.detail import BaseDetailView
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext

from dbaas_cloudstack.models import CloudStackPack
from dbaas_credentials.models import CredentialType
from dbaas import constants
from account.models import Team
from drivers.errors import CredentialAlreadyExists
from physical.models import Host, DiskOffering, Environment, Plan
from util import get_credentials_for
from notification.tasks import TaskRegister
from system.models import Configuration
from logical.errors import DisabledDatabase
from logical.forms.database import DatabaseDetailsForm
from logical.models import Credential, Database, Project
from logical.validators import (check_is_database_enabled, check_is_database_dead,
                                ParameterValidator)


class CredentialView(BaseDetailView):
    model = Credential

    def check_permission(self, request, perm, obj):
        if not request.user.has_perm(perm, obj=obj):
            raise PermissionDenied

    def as_json(self, obj):
        if isinstance(obj, Credential):
            obj = {
                "credential": {"user": obj.user, "password": obj.password, "pk": obj.pk}}
        output = json.dumps(obj, indent=4)
        return HttpResponse(output, content_type="application/json")

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", None)
        database_id = request.POST.get("database_id", None)
        try:
            database = get_object_or_404(Database, pk=database_id)

            # check permission
            self.check_permission(request, "logical.add_credential", database)

            credential = Credential.create_new_credential(username, database)
            return self.as_json(credential)
        except CredentialAlreadyExists:
            return self.as_json({"error": "credential already exists"})
        except ValidationError, e:
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


def check_permission(request, id, tab):
    is_dba = request.user.team_set.filter(role__name="role_dba")

    database = Database.objects.get(id=id)
    if not is_dba:
        can_access = True
        if database.team not in request.user.team_set.all():
            messages.add_message(
                request, messages.ERROR,
                'This database belong to {} team, you are not member of this team'.format(database.team)
            )
            can_access = False
        elif database.is_in_quarantine:
            messages.add_message(
                request, messages.ERROR,
                'This database is in quarantine, please contact your DBA'
            )
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

            return func(request, context, context['database'])
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

    engine = str(database.engine)
    topology = database.databaseinfra.plan.replication_topology
    engine = engine + " - " + topology.details if topology.details else engine
    try:
        masters_quant = len(database.driver.get_master_instance())
    except TypeError:
        masters_quant = 1

    context['masters_quant'] = masters_quant
    context['engine'] = engine
    context['projects'] = Project.objects.all()
    context['teams'] = Team.objects.all()

    return render_to_response(
        "logical/database/details/details_tab.html",
        context, RequestContext(request)
    )


@database_view('credentials')
def database_credentials(request, context, database=None):
    return render_to_response(
        "logical/database/details/credentials_tab.html", context
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
                    if not ParameterValidator.validate_value(parameter_new_value, parameter):
                        error = "Invalid Parameter Value for {}".format(parameter.name)
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

        topology_parameters = database.plan.replication_topology.parameter.all()
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
            can_do_change_parameters_retry, error = database.can_do_change_parameters_retry()
            if not can_do_change_parameters_retry:
                messages.add_message(request, messages.ERROR, error)
                return self.get(request)
            else:
                changed_parameters, error = self.update_database_parameters(request.POST, database)
                if error:
                    messages.add_message(request, messages.ERROR, error)
                    return self.get(request)
                return HttpResponseRedirect(
                    reverse('admin:change_parameters_retry',
                            kwargs={'id': database.id})
                )
        else:
            self.form_status = self.EDITABLE
            can_do_change_parameters, error = database.can_do_change_parameters()
            if not can_do_change_parameters:
                messages.add_message(request, messages.ERROR, error)
                return self.get(request)
            else:
                changed_parameters, error = self.update_database_parameters(request.POST, database)
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
        return super(DatabaseParameters, self).dispatch(request, *args, **kwargs)


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
        reverse('admin:logical_database_parameters', kwargs={'id': database.id})
    )


@database_view("")
def database_change_parameters_retry(request, context, database):
    can_do_change_parameters, error = database.can_do_change_parameters_retry()
    if can_do_change_parameters:
        changed_parameters, parameter_error = DatabaseParameters.update_database_parameters(request.POST, database)

        if parameter_error:
            messages.add_message(request, messages.ERROR, error)
            return HttpResponseRedirect(
                reverse('admin:change_parameters_retry',
                        kwargs={'id': database.id})
            )

        last_change_parameters = database.change_parameters.last()

        if not last_change_parameters.is_status_error:
            error = "Cannot do retry, last change parameters status is '{}'!".format(
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
        reverse('admin:logical_database_parameters', kwargs={'id': database.id})
    )


@database_view('metrics')
def database_metrics(request, context, database):
    context['hostname'] = request.GET.get(
        'hostname',
        database.infra.instances.first().hostname.hostname.split('.')[0]
    )

    context['hosts'] = []
    for host in Host.objects.filter(instances__databaseinfra=database.infra).distinct():
        context['hosts'].append(host.hostname.split('.')[0])

    credential = get_credentials_for(
        environment=database.databaseinfra.environment,
        credential_type=CredentialType.GRAFANA
    )
    instance = database.infra.instances.filter(
        hostname__hostname__contains=context['hostname']
    ).first()

    context['grafana_url'] = '{}/dashboard/{}?{}={}&{}={}&{}={}&{}={}'.format(
        credential.endpoint,
        credential.project.format(database.engine_type),
        credential.get_parameter_by_name('db_param'), instance.dns,
        credential.get_parameter_by_name('os_param'), instance.hostname.hostname,
        credential.get_parameter_by_name('disk_param'),
        credential.get_parameter_by_name('disk_dir'),
        credential.get_parameter_by_name('env_param'),
        credential.get_parameter_by_name('environment')
    )

    return render_to_response(
        "logical/database/details/metrics_tab.html", context
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
        cloudstack_pack = CloudStackPack.objects.get(
            id=request.POST.get('vm_offering')
        )
        Database.resize(
            database=database,
            cloudstackpack=cloudstack_pack,
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
            cloudstack_pack=last_resize.target_offer,
            original_cloudstackpack=last_resize.source_offer,
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
        reverse('admin:logical_database_resizes', kwargs={'id': database.id})
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
        reverse('admin:logical_database_resizes', kwargs={'id': database.id})
    )


@database_view('resizes/upgrade')
def database_resizes(request, context, database):
    if request.method == 'POST':
        if 'disk_resize' in request.POST and request.POST.get('disk_offering'):
            _disk_resize(request, database)
        elif 'vm_resize' in request.POST and request.POST.get('vm_offering'):
            _vm_resize(request, database)
        else:
            disk_auto_resize = request.POST.get('disk_auto_resize', False)
            database.disk_auto_resize = disk_auto_resize
            database.save()

    context['last_vm_resize'] = database.resizes.last()
    context['vm_offerings'] = list(CloudStackPack.objects.filter(
        offering__region__environment=database.environment,
        engine_type__name=database.engine_type
    ))
    context['current_vm_offering'] = database.infra.cs_dbinfra_offering.get().offering
    for offering in context['vm_offerings']:
        if offering.offering == context['current_vm_offering']:
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

    context['upgrade_mongo_24_to_30'] = \
        database.is_mongodb_24() and \
        request.user.has_perm(constants.PERM_UPGRADE_MONGO24_TO_30)
    context['can_do_upgrade'] = \
        bool(database.infra.plan.engine_equivalent_plan) and \
        request.user.has_perm(constants.PERM_UPGRADE_DATABASE)
    context['last_upgrade'] = database.upgrades.filter(
        source_plan=database.infra.plan
    ).last()

    return render_to_response(
        "logical/database/details/resizes_tab.html",
        context, RequestContext(request)
    )


def _add_read_only_instances(request, database):
    try:
        check_is_database_dead(database.id, 'Add read-only instances')
        check_is_database_enabled(database.id, 'Add read-only instances')
    except DisabledDatabase as err:
        messages.add_message(request, messages.ERROR, err.message)
        return

    if not database.plan.replication_topology.has_horizontal_scalability:
        messages.add_message(
            request, messages.ERROR,
            'Database topology do not have horizontal scalability'
        )
        return

    if 'add_read_qtd' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Quantity is required')
        return

    max_read_hosts = Configuration.get_by_name_as_int('max_read_hosts', 5)
    qtd_new_hosts = int(request.POST['add_read_qtd'])
    current_read_nodes = len(database.infra.instances.filter(read_only=True))
    total_read_hosts = qtd_new_hosts + current_read_nodes
    if total_read_hosts > max_read_hosts:
        messages.add_message(
            request, messages.ERROR,
            'Current limit of read only hosts is {} and you are trying to setup {}'.format(
                max_read_hosts, total_read_hosts
            )
        )
        return

    TaskRegister.database_add_instances(
        database=database,
        user=request.user,
        number_of_instances=qtd_new_hosts
    )


@database_view('hosts')
def database_hosts(request, context, database):
    if request.method == 'POST':
        if 'add_read_only' in request.POST:
            _add_read_only_instances(request, database)

    hosts = OrderedDict()
    instances = database.infra.instances.all().order_by('shard', 'id')
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

    context['core_attribute'] = database.engine.write_node_description
    context['read_only_attribute'] = database.engine.read_node_description
    context['last_reinstall_vm'] = database.reinstall_vm.last()

    context['instances_core'] = []
    context['instances_read_only'] = []
    for host, instances in hosts.items():
        attributes = []
        is_read_only = False
        status = ''
        switch_database = False
        for instance in instances:
            is_read_only = instance.read_only
            status = instance.status_html()

            if not instance.is_database:
                context['non_database_attribute'] = instance.get_instance_type_display()
                attributes.append(context['non_database_attribute'])
            elif instance.is_current_write:
                attributes.append(context['core_attribute'])
                if database.databaseinfra.plan.is_ha:
                    switch_database = True
            else:
                attributes.append(context['read_only_attribute'])

        full_description = host.hostname

        padding = False
        if not instance.is_current_write:
            if instance.shard:
                padding = True

        if len(hosts) > 1:
            full_description += ' - ' + '/'.join(attributes)

        host_data = {
            'id': host.id, 'status': status, 'description': full_description,
            'switch_database': switch_database, 'padding': padding
        }

        if is_read_only:
            context['instances_read_only'].append(host_data)
        else:
            context['instances_core'].append(host_data)

    context['max_read_hosts'] = Configuration.get_by_name_as_int('max_read_hosts', 5)
    enable_host = context['max_read_hosts'] - len(context['instances_read_only'])
    context['enable_host'] = range(1, enable_host+1)

    return render_to_response(
        "logical/database/details/hosts_tab.html", context,
        RequestContext(request)
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
            'Host cannot be deleted because database is in use by another task.'
        )
        can_delete = False

    if can_delete:
        TaskRegister.database_remove_instance(database=database, instance=instance, user=request.user)

    return HttpResponseRedirect(
        reverse('admin:logical_database_hosts', kwargs={'id': database.id})
    )


def _clone_database(request, database):
    can_be_cloned, error = database.can_be_cloned()
    if error:
        messages.add_message(request, messages.ERROR, error)
        return

    if 'clone_name' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Destination is required')
        return

    if 'clone_env' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Environment is required')
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

    return render_to_response(
        "logical/database/details/backup_tab.html",
        context, RequestContext(request)
    )


@database_view('dns')
def database_dns(request, context, database):
    context['can_remove_extra_dns'] = request.user.has_perm('extra_dns.delete_extradns')
    context['can_add_extra_dns'] = request.user.has_perm('extra_dns.add_extradns')

    return render_to_response(
        "logical/database/details/dns_tab.html", context
    )


def _destroy_databases(request, database):
    can_be_deleted, error = database.can_be_deleted()
    if error:
        messages.add_message(request, messages.ERROR, error)
        return

    if 'database_name' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Database name is required')
        return

    if request.POST['database_name'] != database.name:
        messages.add_message(request, messages.ERROR, 'Database name is not equal')
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
            'Can not switch write database because it is in use by another task.'
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
            'Can not retry reinstall VM because there is not any reinstall task in progress.'
        )
        can_reinstall_vm = False

    elif database.is_being_used_elsewhere(['notification.tasks.reinstall_vm_database']):
        messages.add_message(
            request, messages.ERROR,
            'Can not retry reinstall VM because database is in use by another task.'
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
