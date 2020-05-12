# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import DatabaseReinstallVM
from api.maintenance_base import MaintennanceBaseApi


class DatabaseReinstallVMSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseReinstallVM
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'instance',
        )


class DatabaseReinstallVMAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = DatabaseReinstallVM
    serializer_class = DatabaseReinstallVMSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'instance',
    )
