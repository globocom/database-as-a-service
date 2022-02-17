# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from account import models
import logging

LOG = logging.getLogger(__name__)


class TeamUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = ('id', 'email')


class TeamApiSerializer(serializers.ModelSerializer):
    user_list = TeamUserSerializer(source="users", many=True, read_only=True)

    class Meta:
        model = models.Team
        fields = ('id', 'name', 'user_list')


class TeamListAPI(viewsets.ViewSet):
    """
    Environment API
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TeamApiSerializer
    http_method_names = ['get']
    queryset = models.Team.objects.all().prefetch_related()
    model = models.Team

    def list(self, request):
        serializer = self.serializer_class(
            instance=self.queryset, many=True)

        return Response(serializer.data)
