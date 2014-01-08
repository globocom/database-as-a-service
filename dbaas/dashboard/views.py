import logging
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from physical.models import DatabaseInfra

LOG = logging.getLogger(__name__)


@login_required
def dashboard(request):
    env_id = request.GET.get('env_id')
    engine_type = request.GET.get('engine_type')

    dbinfra = DatabaseInfra.objects.all()
    if engine_type:
        dbinfra = dbinfra.filter(engine__engine_type__name=engine_type)
    if env_id:
        dbinfra = dbinfra.filter(environment__id=env_id)

    return render_to_response("dashboard/dashboard.html", {'dbinfra': dbinfra}, context_instance=RequestContext(request))


@login_required
def databaseinfra(request, infra_id):
    return render_to_response("dashboard/dashboard.html", context_instance=RequestContext(request))
