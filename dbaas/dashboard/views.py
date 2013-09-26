import logging

from django.contrib import messages
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from base.service.instance import InstanceService

LOG = logging.getLogger(__name__)

def dashboard(request, *args, **kwargs):

    instance_service = InstanceService(request)
    html = "<h1>Dashboard</h1>"
    for instance in instance_service.list():
        instance_status = instance_service.get_instance_status(instance)
        html += '<p>%s - %s</p>' % (instance_status.version, instance_status.instance_model.name)
    
    return HttpResponse(html)
    #return render_to_response('', locals(), context_instance=RequestContext(request))
