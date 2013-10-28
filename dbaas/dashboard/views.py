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

from physical.service.databaseinfra import DatabaseInfraService

LOG = logging.getLogger(__name__)

@login_required
def dashboard(request, *args, **kwargs):
    databaseinfra_service = DatabaseInfraService(request)
    databaseinfras = []
    
    for databaseinfra in databaseinfra_service.list():
        databaseinfra_status = databaseinfra_service.get_databaseinfra_status(databaseinfra)
        data = SortedDict()
        data["name"] = databaseinfra.name
        data["version"] = databaseinfra_status.version
        data["size"] = databaseinfra_status.size_in_mbytes
        data["databases"] = []
    
        for database_status in databaseinfra_status.databases_status.values():
            data["databases"].append({
                "name" : database_status.name,
                "size" : database_status.size_in_mbytes,
                "usage": round(100 * database_status.size_in_mbytes / databaseinfra_status.size_in_mbytes)
            })
        
        databaseinfras.append(data)
    return render_to_response("dashboard/dashboard.html", locals(), context_instance=RequestContext(request))
