import logging
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

import urllib3
import json

LOG = logging.getLogger(__name__)


@login_required
def graphite_metrics(request):
    http = urllib3.PoolManager()

    response = http.request(method="GET", url="http://graphite.dev.globoi.com/render?from=-10minutes&until=now&target=statsite.dbaas.mongodb.kpm.kpm-01-141339554773.cpu.cpu_usr&format=json",)

    data = json.loads(response.data)
    cpu_usr = []
    for d in data[0]['datapoints']:
        if d[0] is not None:
            cpu_usr.append([d[1] * 1000, d[0]])

    LOG.debug("CPU_USER: {}".format(cpu_usr))


    response = http.request(method="GET", url="http://graphite.dev.globoi.com/render?from=-10minutes&until=now&target=statsite.dbaas.mongodb.kpm.kpm-01-141339554773.cpu.cpu_idle&format=json")

    data = json.loads(response.data)
    cpu_idle = []
    for d in data[0]['datapoints']:
        if d[0] is not None:
            cpu_idle.append([d[1] * 1000, d[0]])

    LOG.debug("CPU_IDLE: {}".format(cpu_idle))


    response = http.request(method="GET", url="http://graphite.dev.globoi.com/render?from=-10minutes&until=now&target=statsite.dbaas.mongodb.kpm.kpm-01-141339554773.cpu.cpu_wait&format=json")

    data = json.loads(response.data)
    cpu_wait = []
    for d in data[0]['datapoints']:
        if d[0] is not None:
            cpu_wait.append([d[1] * 1000, d[0]])

    LOG.debug("CPU_WAIT: {}".format(cpu_wait))

    response = http.request(method="GET", url="http://graphite.dev.globoi.com/render?from=-10minutes&until=now&target=statsite.dbaas.mongodb.kpm.kpm-01-141339554773.cpu.cpu_sys&format=json")

    data = json.loads(response.data)
    cpu_sys = []
    for d in data[0]['datapoints']:
        if d[0] is not None:
            cpu_sys.append([d[1] * 1000, d[0]])

    LOG.debug("CPU_IDLE: {}".format(cpu_idle))

    return render_to_response("metrics/graph01.html", {'cpu_usr': cpu_usr, 'cpu_idle': cpu_idle,
        'cpu_wait': cpu_wait,'cpu_sys': cpu_sys}, context_instance=RequestContext(request))


# @login_required
# def databaseinfra(request, infra_id):
#     dbinfra = DatabaseInfra.objects.get(pk=infra_id)
#     databases = Database.objects.filter(databaseinfra=dbinfra)
#     return render_to_response("dashboard/databaseinfra.html", {'infra': dbinfra, 'databases': databases}, context_instance=RequestContext(request))
