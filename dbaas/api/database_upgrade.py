# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseUpgrade
from api.maintenance_base import MaintennanceBaseApi


class DatabaseUpgradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseUpgrade
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'source_plan',
            'target_plan'
        )


class DatabaseUpgradeAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseUpgrade
    serializer_class = DatabaseUpgradeSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'source_plan',
        'target_plan'
    )
