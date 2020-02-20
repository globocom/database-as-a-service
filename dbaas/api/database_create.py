# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseCreate
from api.maintenance_base import MaintennanceBaseApi


class DatabaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseCreate
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


class DatabaseCreateAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseCreate
    serializer_class = DatabaseCreateSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'name'
    )
