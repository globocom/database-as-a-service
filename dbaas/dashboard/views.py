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
    if env_id and engine_type:
        dbinfra = DatabaseInfra.objects.filter(environment__id=env_id, engine__engine_type__name=engine_type)
    else:
        dbinfra = DatabaseInfra.objects.all()
    return render_to_response("dashboard/dashboard.html", {'dbinfra': dbinfra}, context_instance=RequestContext(request))
