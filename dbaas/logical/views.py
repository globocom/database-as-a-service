# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.detail import BaseDetailView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from dbaas_cloudstack.models import CloudStackPack
from dbaas_credentials.models import CredentialType
from dbaas import constants
from drivers.base import CredentialAlreadyExists
from account.models import Team
from physical.models import Host, DiskOffering, Environment, Plan
from util import get_credentials_for
from notification.models import TaskHistory
from notification.tasks import add_instances_to_database, \
    remove_readonly_instance
from .errors import DisabledDatabase
from .forms.database import DatabaseDetailsForm
from .models import Credential, Database, Project
from .validators import check_is_database_enabled, check_is_database_dead


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
        except CredentialAlreadyExists, e:
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


def database_details(request, id):
    database = Database.objects.get(id=id)

    engine = str(database.engine)
    topology = database.databaseinfra.plan.replication_topology
    engine = engine + " - " + topology.details if topology.details else engine

    context = {
        'database': database,
        'engine': engine,
        'projects': Project.objects.all(),
        'teams': Team.objects.all(),
        'title': database.name,
        'current_tab': 'details',
        'user': request.user,
    }

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

    return render_to_response(
        "logical/database/details/details_tab.html",
        context, RequestContext(request)
    )


def database_credentials(request, id):
    database = Database.objects.get(id=id)

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'credentials',
        'user': request.user
    }
    return render_to_response(
        "logical/database/details/credentials_tab.html", context
    )


def database_resizes(request, id):
    database = Database.objects.get(id=id)

    if request.method == 'POST':
        if 'disk_resize' in request.POST and request.POST.get('disk_offering'):
            try:
                check_is_database_enabled(id, 'disk resize')
            except DisabledDatabase as err:
                messages.add_message(request, messages.ERROR, err.message)
            else:
                Database.disk_resize(
                    database=database,
                    new_disk_offering=request.POST.get('disk_offering'),
                    user=request.user
                )

                url = reverse('admin:notification_taskhistory_changelist')
                return HttpResponseRedirect(
                    "{}?user={}".format(url, request.user.username)
                )
        elif 'vm_resize' in request.POST and request.POST.get('vm_offering'):
            try:
                check_is_database_dead(id, 'VM resize')
                check_is_database_enabled(id, 'VM resize')
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

                url = reverse('admin:notification_taskhistory_changelist')
                return HttpResponseRedirect(
                    "{}?user={}".format(url, request.user.username)
                )

        else:
            disk_auto_resize = request.POST.get('disk_auto_resize', False)
            database.disk_auto_resize = disk_auto_resize
            database.save()

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'resizes/upgrade',
        'user': request.user,
    }

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

    context['disk_offerings'] = DiskOffering.objects.all()

    context['upgrade_mongo_24_to_30'] = \
        database.is_mongodb_24() and \
        request.user.has_perm(constants.PERM_UPGRADE_MONGO24_TO_30)
    context['can_do_upgrade'] = \
        bool(database.infra.plan.engine_equivalent_plan) and \
        request.user.has_perm(constants.PERM_UPGRADE_DATABASE)
    context['last_upgrade'] = database.upgrades.filter(
        source_plan=database.infra.plan
    ).last()
    context['is_dba'] = request.user.team_set.filter(role__name="role_dba")

    return render_to_response(
        "logical/database/details/resizes_tab.html",
        context, RequestContext(request)
    )


def _add_read_only_instances(request, database):

    if not database.plan.is_ha:
        messages.add_message(request, messages.ERROR, 'Database is not HA')
        return

    if 'add_read_qtd' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Quantity is required')
        return

    task = TaskHistory()
    task.task_name = "add_database_instances"
    task.task_status = TaskHistory.STATUS_WAITING
    task.arguments = "Adding instances on database {}".format(database)
    task.user = request.user
    task.save()

    add_instances_to_database.delay(
        database, request.user, task, int(request.POST['add_read_qtd'])
    )
    url = reverse('admin:notification_taskhistory_changelist')
    return HttpResponseRedirect(
        "{}?user={}".format(url, request.user.username)
    )


def database_hosts(request, id):
    database = Database.objects.get(id=id)

    if request.method == 'POST':
        if 'add_read_only' in request.POST:
            response = _add_read_only_instances(request, database)
            if response:
                return response

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'hosts',
        'user': request.user,
        'instances_secondary': [],
        'instances_read_only': [],
        'instances_no_database': [],
        'instance_primary': None
    }

    driver = database.infra.get_driver()
    for instance in database.infra.instances.all():
        if not instance.is_database:
            context['instances_no_database'].append(instance)
            continue

        if not context['instance_primary']:
            try:
                driver.check_instance_is_master(instance=instance)
            except:
                pass
            else:
                context['instance_primary'] = instance
                continue

        if instance.read_only:
            context['instances_read_only'].append(instance)
            continue

        context['instances_secondary'].append(instance)

    return render_to_response(
        "logical/database/details/hosts_tab.html", context,
        RequestContext(request)
    )


def database_delete_host(request, database_id, instance_id):
    database = Database.objects.get(id=database_id)
    instance = database.infra.instances.get(id=instance_id)

    if database.is_beeing_used_elsewhere():
        messages.add_message(
            request, messages.ERROR,
            'Host cannot be deleted because database is in use by another task.'
        )
        return HttpResponseRedirect(
            reverse('admin:logical_database_hosts', kwargs={'id': database.id})
        )

    task = TaskHistory()
    task.task_name = "remove_database_instance"
    task.task_status = TaskHistory.STATUS_WAITING
    task.arguments = "Removing instance {} on database {}".format(
        instance, database
    )
    task.user = request.user
    task.save()

    remove_readonly_instance.delay(instance, request.user, task)
    url = reverse('admin:notification_taskhistory_changelist')
    return HttpResponseRedirect(
        "{}?user={}".format(url, request.user.username)
    )


def _clone_database(request, database):
    can_be_cloned, error = database.can_be_cloned()
    if error:
        messages.add_message(request, messages.ERROR, error)

    if 'clone_name' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Destination is required')
        can_be_cloned = False

    if 'clone_env' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Environment is required')
        can_be_cloned = False

    if 'clone_plan' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Plan is required')
        can_be_cloned = False

    if not can_be_cloned:
        return

    name = request.POST['clone_name']
    environment = Environment.objects.get(id=request.POST['clone_env'])
    plan = Plan.objects.get(id=request.POST['clone_plan'])

    Database.clone(
        database=database, clone_name=name, plan=plan,
        environment=environment, user=request.user
    )
    url = reverse('admin:notification_taskhistory_changelist')
    return HttpResponseRedirect(
        "{}?user={}".format(url, request.user.username)
    )


def _restore_database(request, database):
    can_be_restored, error = database.can_be_restored()
    if error:
        messages.add_message(request, messages.ERROR, error)

    if 'restore_snapshot' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Snapshot is required')
        can_be_restored = False

    if not can_be_restored:
        return

    snapshot = request.POST.get('restore_snapshot')
    Database.restore(database=database, snapshot=snapshot, user=request.user)
    url = reverse('admin:notification_taskhistory_changelist')
    return HttpResponseRedirect(
        "{}?user={}".format(url, request.user.username)
    )


def database_backup(request, id):
    database = Database.objects.get(id=id)

    if request.method == 'POST':
        if 'database_clone' in request.POST:
            response = _clone_database(request, database)
            if response:
                return response
        if 'database_restore' in request.POST:
            response = _restore_database(request, database)
            if response:
                return response
        elif 'backup_path' in request.POST:
            database.backup_path = request.POST['backup_path']
            database.save()

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'backup',
        'user': request.user,
        'snapshots': []
    }

    for instance in database.infra.instances.all():
        for backup in instance.backup_instance.all():
            context['snapshots'].append(backup)
    context['snapshots'] = reversed(context['snapshots'])

    context['environments'] = Environment.objects.all()
    context['plans'] = Plan.objects.filter(
        engine=database.engine, is_active=True,
    )
    return render_to_response(
        "logical/database/details/backup_tab.html",
        context, RequestContext(request)
    )


def database_dns(request, id):
    database = Database.objects.get(id=id)

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'dns',
        'user': request.user,
        'can_remove_extra_dns': request.user.has_perm('extra_dns.delete_extradns'),
        'can_add_extra_dns': request.user.has_perm('extra_dns.add_extradns'),
    }
    return render_to_response(
        "logical/database/details/dns_tab.html", context
    )


def database_metrics(request, id):
    database = Database.objects.get(id=id)

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'metrics',
        'user': request.user,
        'hosts': [],
    }

    context['hostname'] = request.GET.get(
        'hostname',
        database.infra.instances.first().hostname.hostname.split('.')[0]
    )

    for host in Host.objects.filter(instances__databaseinfra=database.infra).distinct():
        context['hosts'].append(host.hostname.split('.')[0])

    credential = get_credentials_for(
        environment=database.databaseinfra.environment,
        credential_type=CredentialType.GRAFANA
    )
    instance = database.infra.instances.filter(
        hostname__hostname__contains=context['hostname']
    ).first()

    context['grafana_url'] = '{}/dashboard/{}?{}={}&{}={}&{}={}'.format(
        credential.endpoint,
        credential.project.format(database.engine_type),
        credential.get_parameter_by_name('db_param'), instance.dns,
        credential.get_parameter_by_name('os_param'), instance.hostname.hostname,
        credential.get_parameter_by_name('env_param'),
        credential.get_parameter_by_name('environment')
    )

    return render_to_response(
        "logical/database/details/metrics_tab.html", context
    )


def _destroy_databases(request, database):
    can_be_deleted, error = database.can_be_deleted()
    if error:
        messages.add_message(request, messages.ERROR, error)

    if 'database_name' not in request.POST:
        messages.add_message(request, messages.ERROR, 'Database name is required')
        can_be_deleted = False

    if request.POST['database_name'] != database.name:
        messages.add_message(request, messages.ERROR, 'Database name is not equal')
        can_be_deleted = False

    if not can_be_deleted:
        return

    in_quarantine = database.is_in_quarantine
    database.destroy(request.user)
    if not in_quarantine:
        return

    url = reverse('admin:notification_taskhistory_changelist')
    return HttpResponseRedirect("{}?user={}".format(url, request.user.username))


def database_destroy(request, id):
    database = Database.objects.get(id=id)

    if request.method == 'POST':
        if 'database_destroy' in request.POST:
            response = _destroy_databases(request, database)
            if response:
                return response
        else:
            is_in_quarantine = request.POST.get('is_in_quarantine', False)
            database.is_in_quarantine = is_in_quarantine
            database.save()

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'destroy',
        'user': request.user,
    }
    return render_to_response(
        "logical/database/details/destroy_tab.html",
        context, RequestContext(request)
    )
