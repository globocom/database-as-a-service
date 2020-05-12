# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import RecreateSlave
from api.maintenance_base import MaintennanceBaseApi


class RecreateSlaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecreateSlave
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'task',
            'created_at',
            'host',
        )


class RecreateSlaveAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = RecreateSlave
    serializer_class = RecreateSlaveSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'task',
        'host',
    )
