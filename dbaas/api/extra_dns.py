# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from extra_dns import models


class ExtraDnsSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.ExtraDns
        fields = ('url', 'id', 'database', 'dns')
        read_only = ('database',)

    def save_object(self, obj, force_insert=False, **kwargs):
        if force_insert:
            # ignore password, generating a new random
            self.object = models.ExtraDns(database=obj.database, dns=obj)
        # else:
        #     # it's allowed only change password
        #     self.object.save()
        return self.object


class ExtraDnsAPI(viewsets.ModelViewSet):

    """
    *   ### __List ExtraDns__

        __GET__ /api/extra_dns/

    *   ### __To create a new extra dns on a database__

        __POST__ /api/extra_dns/

            {
                "dns": "{dns}",
                "database": "{api_url}/database/{database_id}/"
            }

    *   ### __To delete a ExtraDns__

        __DELETE__ /api/extra_dns/`extra_dns_id`/

    """
    serializer_class = ExtraDnsSerializer
    queryset = models.ExtraDns.objects.all()

    def check_perm(self, user, perm, extra_dns):
        if not user.has_perm(perm, obj=extra_dns):
            raise exceptions.PermissionDenied

    def create(self, request):
        serializer = self.get_serializer(
            data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.check_perm(
                request.user, 'extra_dns.add_extradns', serializer.object)
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            data = serializer.to_native(self.object)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
