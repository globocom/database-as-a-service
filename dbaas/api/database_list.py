# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from .team import TeamAPI, TeamSerializer

from rest_framework import viewsets, serializers, status, filters
from rest_framework.response import Response
from django.contrib.sites.models import Site

from logical.models import Database
from rest_framework.permissions import IsAuthenticated


LOG = logging.getLogger(__name__)


class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Database
        fields = (
            'url', 'id', 'name', 'team'
        )

    def __init__(self, *args, **kwargs):
        super(DatabaseSerializer, self).__init__(*args, **kwargs)


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

    def get(self):
        queryset = self.model.objects.all()
        return queryset
