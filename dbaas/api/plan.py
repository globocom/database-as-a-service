# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from physical import models
from .environment import EnvironmentSerializer


class PlanSerializer(serializers.HyperlinkedModelSerializer):

    environments = EnvironmentSerializer(many=True, read_only=True)

    class Meta:
        model = models.Plan
        fields = (
            'url', 'id', 'name', 'description', 'is_active', 'engine',
            'environments',
        )


class PlanAPI(viewsets.ReadOnlyModelViewSet):

    """
    Plan API
    """
    serializer_class = PlanSerializer
    queryset = models.Plan.objects.all()

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = models.Plan.objects.all()
        engine_id = self.request.QUERY_PARAMS.get('engine_id', None)
        environment_id = self.request.QUERY_PARAMS.get('environment_id', None)
        old_plan = self.request.QUERY_PARAMS.get('old_plan', None)
        active = self.request.QUERY_PARAMS.get('active', None)

        try:
            if (engine_id is not None) and (environment_id is not None) and (old_plan is not None):
                queryset = models.Plan.objects.filter(engine=engine_id,
                                                      environments=models.Environment.objects.get(id=environment_id)).exclude(id=old_plan)

            elif (engine_id is not None) and (environment_id is not None) and (active is not None):
                queryset = models.Plan.objects.filter(engine=engine_id,
                                                      environments=models.Environment.objects.get(id=environment_id), is_active=bool(active))

            elif engine_id is not None:
                queryset = models.Plan.objects.filter(engine=engine_id)

            elif environment_id is not None:
                queryset = models.Plan.objects.filter(
                    environments=models.Environment.objects.get(id=environment_id))
        except:
            pass

        return queryset
