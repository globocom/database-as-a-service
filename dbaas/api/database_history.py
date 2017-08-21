# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, permissions
from logical.models import DatabaseHistory


class DatabaseHistorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = DatabaseHistory


class DatabaseHistoryAPI(viewsets.ReadOnlyModelViewSet):

    """
    DatabaseHistory API
    """
    serializer_class = DatabaseHistorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = DatabaseHistory.objects.all()
    filter_fields = ('database_id')
