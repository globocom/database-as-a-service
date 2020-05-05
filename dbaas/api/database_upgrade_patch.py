# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseUpgradePatch
from api.maintenance_base import MaintennanceBaseApi


class DatabaseUpgradePatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseUpgradePatch
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'source_patch',
            'target_patch'
        )


class DatabaseUpgradePatchAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseUpgradePatch
    serializer_class = DatabaseUpgradePatchSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'source_patch',
        'target_patch'
    )
