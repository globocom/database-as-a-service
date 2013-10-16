# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, link

class ResourcesViewSet(viewsets.ViewSet):

    @action()
    def resources(self, request, pk=None):
        return Response({"status": "ok"})
    
    @link()
    def status(self, request, pk=None):
        return Response({"status": "ok"})
    