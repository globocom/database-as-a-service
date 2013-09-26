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
        html += '<h2>%s</h2>' % instance.name
        html += '<p>version = %s</p>' % instance_status.version
        html += '<p>size (mb) = %s</p>' % instance_status.size_in_mbytes

        for database_status in instance_status.databases_status.values():
            html += '<h3>%s</h3>' % database_status.name
            html += '<p>size (mb) = %s</p>' % (database_status.size_in_mbytes)
    
    return HttpResponse(html)
    #return render_to_response('', locals(), context_instance=RequestContext(request))
