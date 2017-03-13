# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from backup.models import Snapshot


class SnapshotSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Snapshot
        fields = ('id', 'start_at', 'end_at', 'status')


class SnapshotAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = SnapshotSerializer
    queryset = Snapshot.objects.filter(status=Snapshot.SUCCESS)
