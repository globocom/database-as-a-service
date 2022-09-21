# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import logging

from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import views, serializers, status, permissions
from rest_framework.response import Response

from logical.models import Database
from notification.models import TaskHistory

LOG = logging.getLogger(__name__)


class ZabbixHostInformationSerializer(serializers.Serializer):
    host = serializers.CharField()
    value = serializers.CharField()
    ip = serializers.CharField()
    host_id = serializers.CharField()


class ZabbixDiskSizeAlertSerializer(serializers.Serializer):
    hosts = ZabbixHostInformationSerializer(many=True)


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
            for host in serializer.data:
                # TODO
                database = {'name': ''}
                if not self.validate_running_resize_task(database):
                    LOG.warning("Database {} already has a resize task runing.".format(database['name']))
            return Response(status=status.HTTP_201_CREATED)

        LOG.error("Serializer erros: {}".format(serializer.errors))
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_running_resize_task(self, database):
        running_task = TaskHistory.objects.filter(database=database, task_name='database_disk_resize',
                                                  status__in=self.running_status).first()

        if running_task:
            return False

        return True
