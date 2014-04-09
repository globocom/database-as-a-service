# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from integrations.credentials.models import IntegrationCredential
from .environment import EnvironmentSerializer
from .integration_type import IntegrationTypeSerializer


class IntegrationCredentialSerializer(serializers.HyperlinkedModelSerializer):

    environments = EnvironmentSerializer(many=True, read_only=True)
    integration_type = IntegrationTypeSerializer(many=False, read_only=True)

    class Meta:
        model = IntegrationCredential
        fields = ('user', 'password', 'integration_type', 'token', 'secret', 'endpoint', 'environments',"project",)


class IntegrationCredentialAPI(viewsets.ModelViewSet):
    """
    Integration Credential Api
    """
    serializer_class = IntegrationCredentialSerializer
    queryset = IntegrationCredential.objects.all()


