# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import RemoveInstanceDatabase
from api.maintenance_base import MaintennanceBaseApi


class RemoveInstanceDatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoveInstanceDatabase
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
        )


class RemoveInstanceDatabaseAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = RemoveInstanceDatabase
    serializer_class = RemoveInstanceDatabaseSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
    )
