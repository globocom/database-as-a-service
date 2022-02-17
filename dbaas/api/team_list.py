# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view
from account import models
import logging

LOG = logging.getLogger(__name__)


class TeamApiSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Team
        fields = ('id', 'name',)


class TeamListAPI(viewsets.ReadOnlyModelViewSet):
    """
    Environment API
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TeamApiSerializer
    http_method_names = ['get']
    queryset = models.Team.objects.all()
    model = models.Team

    def get_queryset(self):
        qs = self.queryset
        return qs
