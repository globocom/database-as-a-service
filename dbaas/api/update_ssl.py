# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import UpdateSsl
from api.maintenance_base import MaintennanceBaseApi


class UpdateSslSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpdateSsl
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


class UpdateSslAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = UpdateSsl
    serializer_class = UpdateSslSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'task_schedule'
    )
