# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, permissions
from rest_framework import filters
from notification.models import TaskHistory
from logical.models import Database


class TaskSerializer(serializers.ModelSerializer):
    database = serializers.SerializerMethodField('get_database')
    rollback = serializers.SerializerMethodField('had_rollback')

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
            'task_name',
            'database',
            'rollback',
        )

    def had_rollback(self, task):
        # TODO: see if do details.lower() is expensive
        return (task.task_name != 'notification.tasks.destroy_database' and
                'rollback step' in task.details.lower())

    def get_database(self, task):
        if task.object_class == Database._meta.db_table:
            try:
                database = (
                    Database.objects
                    .select_related(
                        'environment',
                        'databaseinfra',
                        'databaseinfra__engine',
                        'databaseinfra__engine__enginetype'
                    ).get(id=task.object_id)
                )
            except Database.DoesNotExist:
                return None
        else:
            return None

        engine = database.databaseinfra.engine
        return {
            'name': database.name,
            'environment': database.environment.name,
            'engine': '{} {}'.format(
                engine.engine_type.name,
                engine.version
            )
        }


class TaskAPI(viewsets.ReadOnlyModelViewSet):

    """
    Task API
    """

    model = TaskHistory
    serializer_class = TaskSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        'task_id',
        'task_status',
        'object_class',
        'object_id',
        'updated_at',
        'created_at',
        'user'
    )
    ordering_fields = ('created_at', 'updated_at', 'id')
    ordering = ('-created_at',)
    datetime_fields = ('created_at', 'updated_at')

    def get_queryset(self):
        params = self.request.GET.dict()
        filter_params = {}
        for k, v in params.iteritems():
            if k.split('__')[0] in self.filter_fields:
                filter_params[k] = v
        return self.model.objects.filter(**filter_params)
