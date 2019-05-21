# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseChangeParameter
from api.maintenance_base import MaintennanceBaseApi


class DatabaseChangeParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseChangeParameter
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at'
        )


class DatabaseChangeParameterAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseChangeParameter
    serializer_class = DatabaseChangeParameterSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
    )
