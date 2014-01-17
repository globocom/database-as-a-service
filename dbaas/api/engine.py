# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from physical import models
from .engine_type import EngineTypeSerializer

class EngineSerializer(serializers.HyperlinkedModelSerializer):

    engine_type = EngineTypeSerializer(read_only=True)

    class Meta:
        model = models.Engine
        fields = ('url', 'id', 'engine_type', 'version',)


class EngineAPI(viewsets.ReadOnlyModelViewSet):
    """
    Engine API
    """
    serializer_class = EngineSerializer
    queryset = models.Engine.objects.all()


