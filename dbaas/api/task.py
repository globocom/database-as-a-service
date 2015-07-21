# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import filters
from notification.models import TaskHistory


class TaskSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TaskHistory
        fields = ('task_id', 'task_status', 'db_id')

    def get_id(self, obj):
        return obj.task_id


class TaskAPI(viewsets.ReadOnlyModelViewSet):

    """
    Task API
    """
    serializer_class = TaskSerializer
    #queryset = models.Engine.objects.all()
    queryset = TaskHistory.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('task_id', 'task_status')
