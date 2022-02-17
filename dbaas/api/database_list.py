# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status, filters
from rest_framework.permissions import IsAuthenticated
import logging
from logical.models import Database
from physical import models as physical_models
from .engine_type import EngineTypeSerializer
from .engine import EngineSerializer


LOG = logging.getLogger(__name__)


class DatabaseEngineTeamSerializer(EngineTypeSerializer):
    class Meta:
        model = physical_models.EngineType
        fields = ('id', 'name')


class DatabaseEngineSerializer(EngineSerializer):
    engine_type = DatabaseEngineTeamSerializer(read_only=True)

    class Meta:
        model = physical_models.Engine
        fields = ('id', 'engine_type', 'version')


class DatabaseSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name')
    engine = DatabaseEngineSerializer(
        source="engine", many=False, read_only=True)

    class Meta:
        model = Database
        fields = (
            'id', 'name', 'team',
            'description', 'engine'
        )


class DatabaseListAPI(viewsets.ReadOnlyModelViewSet):

    """
    *   ### __List databases__
        __GET__ /api/database_list/
    """
    permission_classes = [IsAuthenticated]
    model = Database
    serializer_class = DatabaseSerializer
    # queryset = Database.objects.all()
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        "name",
        "project",
        "team",
        "engine",
        "environment"
    )
    http_method_names = ['get']

    def get_queryset(self):
        qs = self.model.objects.all()\
            .select_related("databaseinfra__engine")
        return qs
