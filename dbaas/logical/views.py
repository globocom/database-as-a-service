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
from dbaas import constants
from drivers.base import CredentialAlreadyExists
from account.models import Team
from .models import Credential, Database, Project
from .forms.database import DatabaseDetailsForm


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

    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'resizes/upgrade',
        'user': request.user,
    }

    if request.method == 'POST':
        disk_auto_resize = request.POST.get('disk_auto_resize', False)
        database.disk_auto_resize = disk_auto_resize
        database.save()

    context['last_resize'] = database.resizes.last()
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


def database_hosts(request, id):
    database = Database.objects.get(id=id)
    context = {
        'database': database,
        'title': database.name,
        'current_tab': 'hosts',
        'user': request.user
    }
    return render_to_response(
        "logical/database/details/hosts_tab.html",
        context, RequestContext(request)
    )
