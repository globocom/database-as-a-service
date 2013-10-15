import logging

from django.contrib import messages
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import SortedDict

from physical.service.instance import InstanceService

LOG = logging.getLogger(__name__)

@login_required
def dashboard(request, *args, **kwargs):
    instance_service = InstanceService(request)
    instances = []
    
    for instance in instance_service.list():
        instance_status = instance_service.get_instance_status(instance)
        data = SortedDict()
        data["name"] = instance.name
        data["version"] = instance_status.version
        data["size"] = instance_status.size_in_mbytes
        data["databases"] = []
    
        for database_status in instance_status.databases_status.values():
            data["databases"].append({
                "name" : database_status.name,
                "size" : database_status.size_in_mbytes,
                "usage": round(100 * database_status.size_in_mbytes / instance_status.size_in_mbytes)
            })
        
        instances.append(data)
    return render_to_response("dashboard/dashboard.html", locals(), context_instance=RequestContext(request))
