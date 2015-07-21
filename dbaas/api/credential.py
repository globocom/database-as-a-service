# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from logical import models


class CredentialSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Credential
        fields = ('url', 'id', 'user', 'database', 'password',)
        read_only = ('user', 'database',)

    def save_object(self, obj, force_insert=False, **kwargs):
        if force_insert:
            # ignore password, generating a new random
            self.object = models.Credential.create_new_credential(
                obj.user, obj.database)
        # else:
        #     # it's allowed only change password
        #     self.object.save()
        return self.object


class CredentialAPI(viewsets.ModelViewSet):

    """
    *   ### __List Credentials__

        __GET__ /api/credential/

    *   ### __To create a new credential on a database__

        __POST__ /api/credential/

            {
                "user": "{username}",
                "database": "{api_url}/database/{database_id}/"
            }

    *   ### __Show details (including password) about a credential__

        __GET__ /api/credential/`credential_id`/

    *   ### __To delete a Credential__

        __DELETE__ /api/credential/`credential_id`/

    *   ### __To reset password__

        __POST__ /api/credential/`database_id`/reset_password

    """
    serializer_class = CredentialSerializer
    queryset = models.Credential.objects.all()
    actions_to_show_password = (
        'retrieve', 'create', 'update', 'reset_password')

    def get_serializer(self, *args, **kwargs):
        serializer = super(CredentialAPI, self).get_serializer(*args, **kwargs)
        if self.action in self.actions_to_show_password:
            serializer.fields['password'] = serializers.Field(
                source='password')
        return serializer

    def check_perm(self, user, perm, credential):
        if not user.has_perm(perm, obj=credential):
            raise exceptions.PermissionDenied

    def create(self, request):
        serializer = self.get_serializer(
            data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.check_perm(
                request.user, 'logical.add_credential', serializer.object)
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            data = serializer.to_native(self.object)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action()
    def reset_password(self, request, pk=None):
        credential = self.get_object()
        credential.reset_password()
        serializer = self.get_serializer(instance=credential)
        return Response(serializer.data)
