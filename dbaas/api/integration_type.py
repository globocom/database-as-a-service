# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from integrations.credentials.models import IntegrationType


class IntegrationTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = IntegrationType
        fields = ('name', 'type')


class IntegrationTypeAPI(viewsets.ModelViewSet):
    """
    IntegrationTypeApi
    """
    serializer_class = IntegrationTypeSerializer
    queryset = IntegrationType.objects.all()


