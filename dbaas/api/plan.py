# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from physical import models
from .environment import EnvironmentSerializer


class PlanSerializer(serializers.HyperlinkedModelSerializer):
    
    environments = EnvironmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = models.Plan
        fields = ('url', 'id', 'name', 'description', 'is_active', 'is_default', 'engine_type', 'environments',)


class PlanAPI(viewsets.ReadOnlyModelViewSet):
    """
    Plan API
    """
    serializer_class = PlanSerializer
    queryset = models.Plan.objects.all()

    def list(self, request):
        queryset = models.Plan.objects.all()
        engine_id = request.QUERY_PARAMS.get('engine_id', None)

        if engine_id is not None:
            try:
                queryset = models.Plan.objects.filter(engine_type=models.Engine.objects.get(id=engine_id).engine_type)
            except:
                pass

        serializer = PlanSerializer(queryset, many=True)
        return Response(serializer.data)


