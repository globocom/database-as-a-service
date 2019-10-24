# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters
from rest_framework.views import APIView
from util import get_credentials_for
from dbaas_credentials.models import CredentialType, Credential
from notification.tasks import TaskRegister

from physical.models import Host



class HostSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField('get_team_name')
    env_name = serializers.SerializerMethodField('get_env_name')
    offering = serializers.SerializerMethodField('get_offering')
    disks = serializers.SerializerMethodField('get_disks')
    project_id = serializers.SerializerMethodField('get_project_id')
    database = serializers.SerializerMethodField('get_database_metadata')

    class Meta:
        model = Host
        fields = (
            'id',
            'os_description',
            'updated_at',
            'created_at',
            'team_name',
            'env_name',
            'hostname',
            'offering',
            'disks',
            'project_id',
            'database',
            'identifier'
        )

    def get_database(self, host):
        first_instance = host.instances.first()
        database = (first_instance
                    and first_instance.databaseinfra.databases.first())

        return database

    def get_database_metadata(self, host):
        database = self.get_database(host)

        if database is None:
            return {}
        return {
            'project_name': database.project and database.project.name,
            'engine': str(database.engine),
            'name': database.name,
            'id': database.id,
            'infra': {
                'id': database.infra.id,
                'name': database.infra.name
            }
        }

    def get_team_name(self, host):
        database = self.get_database(host)

        return database and database.team.name

    def get_env(self, host):
        database = self.get_database(host)

        return database and database.environment

    def get_env_name(self, host):
        env = self.get_env(host)

        return env and env.name

    def get_project_id(self, host):
        env = self.get_env(host)

        try:
            credential = get_credentials_for(
                env, CredentialType.CLOUDSTACK)
        except IndexError:
            return None

        return credential and credential.project

    def get_disks(self, host):
        return map(
            lambda d: {
                'active': d.is_active,
                'total': d.total_size_kb,
                'used': d.used_size_kb,
                'export_id': d.identifier
            }, host.volumes.all())

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
    queryset = Host.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        'id',
        'os_description',
        'updated_at',
        'created_at',
        'hostname'
    )
    ordering_fields = ('created_at', 'updated_at', 'id')
    ordering = ('-created_at',)
    datetime_fields = ('created_at', 'updated_at')

    def get_queryset(self, *args, **kw):
        def has_database(host):
            first_instance = host.instances.first()
            if not first_instance:
                return False
            return (first_instance
                    and first_instance.databaseinfra.databases.exists())
        params = self.request.GET.dict()
        filter_params = {}
        for k, v in params.iteritems():
            if k == 'cloudstack_hosts_only':
                cs_envs = Credential.objects.filter(
                    integration_type__type=CredentialType.HOST_PROVIDER,
                    project='cloudstack'
                ).values_list(
                    'environments', flat=True
                )
                filter_params[
                    'instances__databaseinfra__environment__in'
                ] = cs_envs
            elif k.split('__')[0] in self.filter_fields:
                filter_params[k] = v
        hosts = self.model.objects.filter(**filter_params).distinct()
        filtered_hosts = filter(lambda h: has_database(h), hosts)
        host_ids = map(lambda h: h.id, filtered_hosts)

        return hosts.filter(id__in=host_ids)

    def _render_error(self, msg, status):
        return Response(
            {'error_msg': msg},
            status=status
        )

    @action(methods=['post'])
    def recreate_slave(self, request, pk=None):
        host = self.get_object()
        if not host.is_database:
            return self._render_error(
                "The host must be Database instance",
                422
            )
        serializer = self.get_serializer()
        database = serializer.get_database(host)
        if database.is_being_used_elsewhere():
            return self._render_error(
                "Database {} is being used for another task".format(database),
                422
            )
        if not (database.databaseinfra.plan.replication_topology
                .can_recreate_slave):
            return self._render_error(
                "This topology cant recreate slave",
                422
            )
        instance = host.database_instance()
        driver = instance.databaseinfra.get_driver()
        if driver.check_instance_is_master(instance):
            return self._render_error(
                "Host is master. The host must be Slave",
                422
            )
            raise Exception()
        TaskRegister.recreate_slave(host=host, user=request.user)
        return Response(
            {'hostname': host.hostname, 'id': host.id},
            status=204
        )


class CheckIsSlaveAPIView(APIView):
    """
    View to check whether a host is slave or not

    * Requires being authenticated or with read-only permission.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def check_is_slave(self, host):
        db_instance = host.database_instance()
        return db_instance.is_slave

    def get(self, request, hostname, format=None):
        host = Host.objects.filter(hostname=hostname).first()
        if not host:
            return Response(
                {'error_msg': "The hostname was not found!"},
                status=404
            )

        if not host.is_database:
            return Response(
                {'error_msg': "The host must be Database instance"},
                status=422
            )

        is_slave = self.check_is_slave(host)
        return Response(
            {'is_slave': is_slave, 'hostname': host.hostname},
            status=200
        )
