# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

from rest_framework import viewsets, serializers, status
from rest_framework.response import Response

LOG = logging.getLogger(__name__)


class ZabbixDiskSizeAlertSerializer(serializers.Serializer):
    host = serializers.CharField()
    value = serializers.CharField()
    ip = serializers.CharField()
    host_id = serializers.CharField()


class ZabbixDiskSizeAlertAPI(viewsets.ViewSet):

    def create(self, request, *args, **kwargs):
        data = request.data
        LOG.info(data)
        serializer = ZabbixDiskSizeAlertSerializer(data, many=True)
        if serializer.is_valid():
            return Response(status=status.HTTP_201_CREATED)
