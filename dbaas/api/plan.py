# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from physical import models


class PlanSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Plan
        fields = ('url', 'id', 'name', 'description', 'is_active', 'is_default', 'engine_type', 'environments',)


class PlanAPI(viewsets.ModelViewSet):
    """
    Plan API
    """
    serializer_class = PlanSerializer
    queryset = models.Plan.objects.all()


