# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from physical import models


class EngineSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Engine
        fields = ('url', 'id', 'engine_type', 'version',)


class EngineAPI(viewsets.ModelViewSet):
    """
    Engine API
    """
    serializer_class = EngineSerializer
    queryset = models.Engine.objects.all()


