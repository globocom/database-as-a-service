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
    except Exception, e:
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
