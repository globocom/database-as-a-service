# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, permissions
from rest_framework import filters
from notification.models import TaskHistory


class TaskSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TaskHistory
        fields = (
            'id',
            'task_id',
            'task_status',
            'db_id',
            'object_class',
            'object_id',
            'updated_at',
            'user',
            'created_at',
            'task_name'
        )

    def get_id(self, obj):
        return obj.task_id


class TaskAPI(viewsets.ReadOnlyModelViewSet):

    """
    Task API
    """

    model = TaskHistory
    serializer_class = TaskSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # queryset = TaskHistory.objects.all().order_by('-
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        'task_id',
        'task_status',
        'object_class',
        'object_id',
        'updated_at',
        'created_at'
    )
    ordering_fields = ('created_at', 'updated_at', 'id')
    ordering = ('-created_at',)
    datetime_fields = ('created_at', 'updated_at')

    def get_queryset(self):
        params = self.request.GET.dict()
        filter_params = {}
        for k, v in params.iteritems():
            if k.split('__')[0] in self.datetime_fields:
                filter_params[k] = v
        return self.model.objects.filter(**filter_params)
