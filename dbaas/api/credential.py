# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
# from rest_framework.response import Response
from logical import models


class CredentialSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Credential
        fields = ('url', 'id', 'user', 'password', 'database')

    def __init__(self, *args, **kwargs):
        super(CredentialSerializer, self).__init__(*args, **kwargs)

    def save_object(self, obj, created=False, **kwargs):
        if created:
            # ignore password, generating a new random
            self.object = models.Credential.create_new_credential(obj.user, obj.database)
        else:
            # it's allowed only change password
            self.object.save()


class CredentialAPI(viewsets.ModelViewSet):
    """
    Credential API
    """
    serializer_class = CredentialSerializer
    queryset = models.Credential.objects.all()

