# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseMigrateEngine
from api.maintenance_base import MaintennanceBaseApi


class DatabaseMigrateEngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseMigrateEngine
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'source_plan',
            'target_plan',
            'source_plan_name',
            'target_plan_name'
        )


class DatabaseMigrateEngineAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseMigrateEngine
    serializer_class = DatabaseMigrateEngineSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'source_plan',
        'target_plan',
        'source_plan_name',
        'target_plan_name'
    )
