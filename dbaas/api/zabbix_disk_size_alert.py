# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import logging

from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import views, serializers, status, permissions
from rest_framework.response import Response

from logical.models import Database
from maintenance.tasks import TaskRegisterMaintenance
from physical.models import Host

LOG = logging.getLogger(__name__)


class ZabbixHostInformationSerializer(serializers.Serializer):
    host = serializers.CharField()
    value = serializers.CharField()
    ip = serializers.CharField()
    host_id = serializers.CharField()


class ZabbixDiskSizeAlertSerializer(serializers.Serializer):
    host = ZabbixHostInformationSerializer()


class ZabbixDiskSizeAlertAPIView(views.APIView):
    model = Database
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication,)

    running_status = ('RUNNING', 'WAITING')

    def post(self, request, *args, **kwargs):
        LOG.info("Resize Zabbix Alert -> Received payload: {}".format(request.DATA))
        data = request.DATA

        serializer = ZabbixDiskSizeAlertSerializer(data=data)
        if serializer.is_valid():
            host = serializer.data['host']

            # busca a database pelo IP do Host
            database = self.get_database_from_host_ip(host['ip'])
            if database is None:
                return Response({'message': 'Database não encontrada'}, status=status.HTTP_404_NOT_FOUND)

            # Valida se nao tem nenhuma task de resize rodando para a database
            running = self.validate_running_resize_task(database)

            TaskRegisterMaintenance.zabbix_alert_resize_disk(database, running)

            LOG.info("No resize task is running for database {}".format(database.name))

            return Response(status=status.HTTP_201_CREATED)

        LOG.error("Serializer erros: {}".format(serializer.errors))
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_running_resize_task(self, database):
        from notification.models import TaskHistory
        # busca task de resize de disco para a database
        running_task = TaskHistory.objects.filter(database_name=database.name, task_name='database_disk_resize',
                                                  task_status__in=self.running_status).first()

        if running_task:
            return False

        return True

    def get_database_from_host_ip(self, ip):
        # busca host pelo ip
        host = Host.objects.filter(address=ip).first()
        if not host:
            LOG.error("Host with IP {} not found!".format(ip))
            return None
        LOG.info("Host with IP {} is {}".format(ip, host.hostname))

        # busca database atraves da databaseinfra do host
        database = Database.objects.filter(databaseinfra=host.databaseinfra).first()
        if not database:
            LOG.error("Database with Host {} not found!".format(host.id))
        LOG.info("Database for Host {} is {}".format(host.hostname, database.name))

        return database
