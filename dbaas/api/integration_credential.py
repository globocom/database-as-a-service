# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from dbaas_credentials.models import Credential
from .environment import EnvironmentSerializer
from .integration_type import CredentialTypeSerializer


class CredentialSerializer(serializers.HyperlinkedModelSerializer):

    environments = EnvironmentSerializer(many=True, read_only=True)
    integration_type = CredentialTypeSerializer(many=False, read_only=True)

    class Meta:
        model = Credential
        fields = ('user', 'password', 'integration_type', 'token', 'secret', 'endpoint', 'environments',"project","team")


class CredentialAPI(viewsets.ModelViewSet):
    """
    Integration Credential Api
    """
    serializer_class = CredentialSerializer
    queryset = Credential.objects.all()


