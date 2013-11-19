# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response
from logical import models


class CredentialSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Credential
        fields = ('url', 'id', 'user', 'password', 'database',)

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

    def create(self, request):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

