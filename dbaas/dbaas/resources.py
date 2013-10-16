# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, link

from physical.models import Engine, EngineType

LOG = logging.getLogger(__name__)

class TsuruViewSet(viewsets.ViewSet):
    
    AVAILABLES_APIS = ['mongodb']
    
    def list(self, request):
        return Response({"status": "list"})
    
    def create(self, request):
        """
         Creates a new instance

         Return codes:
         201: when the instance is successfully created. You don’t need to include any content in the response body.
         500: in case of any failure in the creation process. Make sure you include an explanation for the failure in the response body.
         """
        return Response({"status": "create"})
            
    @action()
    def resources(self, request, pk=None):
        """
        Creates a new instance. The pk is the name of the engine
        
        Return codes:
        201: when the instance is successfully created. You don’t need to include any content in the response body.
        500: in case of any failure in the creation process. Make sure you include an explanation for the failure in the response body.
        """
        LOG.info("Call for %s api" % pk)
        if pk not in TsuruViewSet.AVAILABLES_APIS:
            return Response(data={"error": "endpoint not available for %s" % pk}, status=500)
        
        try:
            engine_type = EngineType.objects.get(name=pk)
        except EngineType.DoesNotExists:
            return Response(data={"error": "endpoint not found" % pk}, status=404)
        
        return Response({"status": "ok", "engine_type": engine_type.name})
    
    @link()
    def status(self, request, pk=None):
        return Response({"status": "ok"})
    