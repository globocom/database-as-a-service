# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, link

class ResourcesViewSet(viewsets.ViewSet):
    
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
        return Response({"status": "ok"})
    
    @link()
    def status(self, request, pk=None):
        return Response({"status": "ok"})
    