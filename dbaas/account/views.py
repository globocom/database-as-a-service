# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import json
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from account.models import Team
from logical.models import Database

LOG = logging.getLogger(__name__)


@login_required
def profile(request, user_id=None):
    user = None
    databases = None
    teams = None
    roles = None
    try:
        user = User.objects.get(id=user_id)
        teams = Team.objects.filter(users=user)
        databases = Database.alive.filter(
            team__in=[team.id for team in teams]).order_by('team')
        roles = [team.role for team in teams]
    except Exception as e:
        LOG.warning("Ops... %s" % e)

    return render_to_response(
        "account/profile.html",
        locals(),
        context_instance=RequestContext(request)
    )


def emergency_contacts(team_id):
    try:
        team = Team.objects.get(id=team_id)
    except (ObjectDoesNotExist, ValueError):
        return
    else:
        return team.emergency_contacts


def team_contacts(self, team_id):
    response_json = json.dumps({
        "contacts": emergency_contacts(team_id)
    })
    return HttpResponse(response_json, content_type="application/json")


def team_resources(self, team_id):
    databases = Database.objects.filter(team_id=team_id)
    resources = {'cpu': 0, 'memory': 0, 'disk': 0, 'vms': 0}
    for database in databases:
        hosts = database.databaseinfra.hosts
        for host in hosts:
            resources['cpu'] += host.offering.cpus
            resources['memory'] += round((host.offering.memory_size_mb / 1024), 2)
            resources['disk'] += round(host.root_size_gb, 2)
            resources['vms'] += 1
    response_json = json.dumps(resources)

    return HttpResponse(response_json, content_type="application/json")
