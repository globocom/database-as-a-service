# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import serializers
from maintenance.models import HostMigrate
from api.maintenance_base import MaintennanceBaseApi


class HostMigrateSerializer(serializers.ModelSerializer):

    database = serializers.SerializerMethodField('get_database')

    class Meta:
        model = HostMigrate
        fields = (
            'id',
            'current_step',
            'status',
            'can_do_retry',
            'database',
            'task',
            'created_at',
            'host',
            'environment',
            'zone',
            'database_migrate',
            'snapshot',
            'task_schedule'
        )

    def get_database(self, manager):
        host = manager.host
        if host:
            db = host.instances.first().databaseinfra.databases.first()
            if db:
                return {
                    'id': db.id,
                    'name': db.name,
                    'team_name': db.team.name,
                    'environment': db.infra.environment
                }
        return


class HostMigrateAPI(MaintennanceBaseApi):

    """
    Task API
    """

    model = HostMigrate
    serializer_class = HostMigrateSerializer
    filter_fields = (
        'status',
        'can_do_retry',
        'database',
        'host',
        'zone'
    )
