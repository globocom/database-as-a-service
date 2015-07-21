# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.contrib.auth.models import User
from django.contrib import messages
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.datastructures import SortedDict
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

    return render_to_response("account/profile.html", locals(), context_instance=RequestContext(request))
