# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseDestroy
from api.maintenance_base import MaintennanceBaseApi


class DatabaseDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseDestroy
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'name'
        )


class DatabaseDestroyAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseDestroy
    serializer_class = DatabaseDestroySerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'name'
    )
