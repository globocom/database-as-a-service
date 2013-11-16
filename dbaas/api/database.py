# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response
from logical import models
from physical.models import Plan, Environment


class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    plan = serializers.HyperlinkedRelatedField(
        source='plan', read_only=False, view_name='plan-detail', queryset=Plan.objects)
    environment = serializers.HyperlinkedRelatedField(
        source='environment', read_only=False, view_name='environment-detail', queryset=Environment.objects)

    class Meta:
        model = models.Database
        fields = ('url', 'id', 'name', 'plan', 'environment')


class DatabaseAPI(viewsets.ModelViewSet):
    """
    Database API
    """
    serializer_class = DatabaseSerializer
    queryset = models.Database.objects.all()

    def create(self, request):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        data = serializer.restore_fields(request.DATA, request.FILES)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = models.Database.provision(data['name'], data['plan'], data['environment'])
            data = serializer.to_native(self.object)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
