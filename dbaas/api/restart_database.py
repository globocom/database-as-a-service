# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import RestartDatabase
from api.maintenance_base import MaintennanceBaseApi


class RestartDatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestartDatabase
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'task_schedule'
        )


class RestartDatabaseAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = RestartDatabase
    serializer_class = RestartDatabaseSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'task_schedule'
    )
