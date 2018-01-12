# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, permissions
from rest_framework import filters
from django.core.exceptions import ObjectDoesNotExist

from physical.models import Host


class HostSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField('get_team_name')
    env_name = serializers.SerializerMethodField('get_env_name')
    offering = serializers.SerializerMethodField('get_offering')
    total_disk_kb = serializers.SerializerMethodField('get_total_disk')
    used_disk_kb = serializers.SerializerMethodField('get_used_disk')

    class Meta:
        model = Host
        fields = (
            'id',
            'os_description',
            'updated_at',
            'created_at',
            'team_name',
            'env_name',
            'offering',
            'total_disk_kb',
            'used_disk_kb',
        )

    def get_database(self, host):
        first_instance = host.instances.first()
        database = first_instance and first_instance.databaseinfra.databases.first()

        return database

    def get_team_name(self, host):
        database = self.get_database(host)

        return database and database.team.name

    def get_env_name(self, host):
        database = self.get_database(host)

        return database and database.environment.name

    def get_total_disk(self, host):
        try:
            return host.active_disk.nfsaas_size_kb
        except ObjectDoesNotExist:
            return

    def get_used_disk(self, host):
        try:
            return host.active_disk.nfsaas_used_size_kb
        except ObjectDoesNotExist:
            return

    def get_offering(self, host):
        offering = host.offering
        if offering:
            return {
                'type': '{}c{}'.format(offering.cpus, offering.memory_size_mb),
                'cpus': offering.cpus,
                'memory': offering.memory_size_mb
            }
        return {}


class HostAPI(viewsets.ReadOnlyModelViewSet):

    """
    Host API
    """

    model = Host
    serializer_class = HostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        'id',
        'os_description',
        'updated_at',
        'created_at',
    )
    ordering_fields = ('created_at', 'updated_at', 'id')
    ordering = ('-created_at',)
    datetime_fields = ('created_at', 'updated_at')
