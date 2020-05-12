# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseClone
from api.maintenance_base import MaintennanceBaseApi


class DatabaseCloneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseClone
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'origin_database',
            'infra',
            'plan',
            'environment',
            'name'
        )


class DatabaseCloneAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseClone
    serializer_class = DatabaseCloneSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'origin_database',
        'infra',
        'plan',
        'environment',
        'name'
    )
