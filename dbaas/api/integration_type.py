# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from dbaas_credentials.models import CredentialType


class CredentialTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = CredentialType
        fields = ('name', 'type')


class CredentialTypeAPI(viewsets.ModelViewSet):

    """
    IntegrationTypeApi
    """
    serializer_class = CredentialTypeSerializer
    queryset = CredentialType.objects.all()
