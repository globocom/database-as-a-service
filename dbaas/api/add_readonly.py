# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import AddInstancesToDatabase
from api.maintenance_base import MaintennanceBaseApi


class AddInstancesToDatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddInstancesToDatabase
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
        )


class AddInstancesToDatabaseAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = AddInstancesToDatabase
    serializer_class = AddInstancesToDatabaseSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
    )
