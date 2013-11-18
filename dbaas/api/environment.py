# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from physical import models


class EnvironmentSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Environment
        fields = ('url', 'id', 'name',)


class EnvironmentAPI(viewsets.ModelViewSet):
    """
    Environment API
    """
    serializer_class = EnvironmentSerializer
    queryset = models.Environment.objects.all()


