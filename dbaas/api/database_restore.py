# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, permissions
from rest_framework import filters
from maintenance.models import DatabaseRestore
# from logical.models import Database, DatabaseHistory


class DatabaseRestoreSerializer(serializers.ModelSerializer):
    # database = serializers.SerializerMethodField('get_database')
    # rollback = serializers.SerializerMethodField('had_rollback')
    # relevance = serializers.SerializerMethodField('get_relevance')

    class Meta:
        model = DatabaseRestore
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at'
        )


class DatabaseRestoreAPI(viewsets.ReadOnlyModelViewSet):

    """
    Task API
    """

    model = DatabaseRestore
    serializer_class = DatabaseRestoreSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
    )
    ordering_fields = ('created_at', 'id')
    ordering = ('-created_at',)
    datetime_fields = ('created_at')

    # def get_queryset(self):
    #     params = self.request.GET.dict()
    #     filter_params = {}
    #     for k, v in params.iteritems():
    #         if k == 'exclude_system_tasks':
    #             filter_params['task_name__in'] = self.chg_tasks_names
    #         elif k.split('__')[0] in self.filter_fields:
    #             filter_params[k] = v
    #     return self.model.objects.filter(**filter_params)
