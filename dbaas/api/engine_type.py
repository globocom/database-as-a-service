# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from physical import models


class EngineTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.EngineType
        fields = ('url', 'id', 'name')


class EngineTypeAPI(viewsets.ReadOnlyModelViewSet):

    """
    EngineType API
    """
    serializer_class = EngineTypeSerializer
    queryset = models.EngineType.objects.all()
