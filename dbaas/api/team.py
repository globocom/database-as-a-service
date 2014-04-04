# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from account import models


class TeamSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Team
        fields = ('url', 'id', 'name',)


class TeamAPI(viewsets.ReadOnlyModelViewSet):
    """
    Environment API
    """
    serializer_class = TeamSerializer
    queryset = models.Team.objects.all()
