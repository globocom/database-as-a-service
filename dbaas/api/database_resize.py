# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseResize
from api.maintenance_base import MaintennanceBaseApi


class DatabaseResizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseResize
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'source_offer',
            'target_offer'
        )


class DatabaseResizeAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseResize
    serializer_class = DatabaseResizeSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'source_offer',
        'target_offer'
    )
