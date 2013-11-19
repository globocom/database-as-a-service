# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response
from logical import models
from physical.models import Plan, Environment


class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    plan = serializers.HyperlinkedRelatedField(
        source='plan', read_only=True, view_name='plan-detail', queryset=Plan.objects)
    environment = serializers.HyperlinkedRelatedField(
        source='environment', read_only=True, view_name='environment-detail', queryset=Environment.objects)
    endpoint = serializers.Field(source='endpoint')
    quarantine_dt = serializers.Field(source='quarantine_dt')
    total_size_in_bytes = serializers.Field(source='total_size')
    used_size_in_bytes = serializers.Field(source='used_size')

    class Meta:
        model = models.Database
        fields = ('url', 'id', 'name', 'endpoint', 'plan', 'environment', 'project',
            'quarantine_dt', 'total_size_in_bytes', 'used_size_in_bytes', 'credentials')

    def __init__(self, *args, **kwargs):
        super(DatabaseSerializer, self).__init__(*args, **kwargs)
        
        creating = self.context['request'].method == 'POST'
        # when database is created, user can't change plan, environment and name
        self.fields['plan'].read_only = not creating
        self.fields['environment'].read_only = not creating
        self.fields['name'].read_only = not creating
        self.fields['credentials'].read_only = True

        # quarantine is always readonly
        # self.fields['quarantine_dt'].read_only = True


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
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
