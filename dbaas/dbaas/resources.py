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
    
    def __check_service_availability(self, service_name):
        """
        Checks the availability of the service.
        Returns engine_type for the service or a response error 500 if not found.
        
        """
        engine_type = None
        try:
            engine_type = EngineType.objects.get(name=service_name)
            return engine_type
        except EngineType.DoesNotExist:
            LOG.warning("endpoint not available for %s" % service_name)
        
        return engine_type


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
        engine_type = self.__check_service_availability(pk)
        if not engine_type:
            return Response(data={"error": "endpoint not available for %s" % pk}, status=500)

        return Response({"status": "ok", "engine_type": engine_type.name}, status=201)
    
    @link()
    def status(self, request, pk=None):
        engine_type = self.__check_service_availability(pk)
        if not engine_type:
            return Response(data={"error": "endpoint not available for %s" % pk}, status=500)

        return Response(data={"status": "ok"}, status=204)
    