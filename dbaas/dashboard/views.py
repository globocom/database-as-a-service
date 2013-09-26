import logging

from django.contrib import messages
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string

LOG = logging.getLogger(__name__)

def dashboard(request, *args, **kwargs):
    
    return HttpResponse("<h1>Dashboard</h1>")
    #return render_to_response('', locals(), context_instance=RequestContext(request))
