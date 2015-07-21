# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from physical import models
from .plan import PlanSerializer


class EngineTypeSerializer(serializers.HyperlinkedModelSerializer):

    plans = PlanSerializer(many=True, read_only=True)

    class Meta:
        model = models.EngineType
        fields = ('url', 'id', 'name', 'plans')


class EngineTypeAPI(viewsets.ReadOnlyModelViewSet):

    """
    EngineType API
    """
    serializer_class = EngineTypeSerializer
    queryset = models.EngineType.objects.all()
