# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response
from logical import models
from physical.models import Plan, Environment, DatabaseInfra
from account.models import Team
from .credential import CredentialSerializer
from django.contrib.sites.models import Site
import logging

LOG = logging.getLogger(__name__)

class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    plan = serializers.HyperlinkedRelatedField(
        source='plan', view_name='plan-detail', queryset=Plan.objects)
    environment = serializers.HyperlinkedRelatedField(
        source='environment', view_name='environment-detail', queryset=Environment.objects)
    team = serializers.HyperlinkedRelatedField(
        source='team', view_name='team-detail', queryset=Team.objects)
    endpoint = serializers.Field(source='endpoint')
    quarantine_dt = serializers.Field(source='quarantine_dt')
    total_size_in_bytes = serializers.Field(source='total_size')
    used_size_in_bytes = serializers.Field(source='used_size')
    credentials = CredentialSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField('get_status')

    class Meta:
        model = models.Database
        fields = ('url', 'id', 'name', 'endpoint', 'plan', 'environment', 'project', 'team', 'status',
            'quarantine_dt', 'total_size_in_bytes', 'used_size_in_bytes', 'credentials','description',)
        read_only = ('credentials',)

    def get_status(self, obj):
        if obj is not None:
            return obj.database_status.is_alive

    def __init__(self, *args, **kwargs):
        super(DatabaseSerializer, self).__init__(*args, **kwargs)
        
        request = self.context.get('request', None)
        if request:
            creating = request.method == 'POST'

            # when database is created, user can't change plan, environment and name
            self.fields['plan'].read_only = not creating
            self.fields['environment'].read_only = not creating
            self.fields['name'].read_only = not creating
            self.fields['credentials'].read_only = True
            self.fields['description'].read_only = not creating

        # quarantine is always readonly
        # self.fields['quarantine_dt'].read_only = True


class DatabaseAPI(viewsets.ModelViewSet):
    """
    *   ### __List databases__

        __GET__ /api/database/

    *   ### __To create a new database__

        __POST__ /api/database/

            {
                "name": "{name}",
                "plan": "{api_url}/plan/{plan_id}/",
                "environment": "{api_url}/environment/{environment_id}/",
                "project": "{api_url}/project/{project_id}/",
                "team": "{api_url}/team/{team_id}/",
                "description": "{description}"
            }

    *   ### __Show details about a database__

        __GET__ /api/database/`database_id`/

    *   ### __To delete a database (will put it on quarantine)__

        __DELETE__ /api/database/`database_id`/

    *   ### __To change database project__

        __PUT__ /api/database/`database_id`/

            {
                "project": "{api_url}/project/{project_id}/"
            }

    """
    serializer_class = DatabaseSerializer
    queryset = models.Database.objects.all()

    def create(self, request):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        
        if serializer.is_valid():
            self.pre_save(serializer.object)
            data = serializer.restore_fields(request.DATA, request.FILES)

            LOG.info("Plano %s" % data['plan'])

            plan = data['plan']

            if plan.provider == plan.CLOUDSTACK:
                from notification.tasks import create_database

                result = create_database.delay(data['name'],
                                                   data['plan'],
                                                   data['environment'],
                                                   data['team'],
                                                   data['project'],
                                                   data['description'],
                                                   request.user)
        
                #data = serializer.to_native(self.object)
                #self.post_save(self.object, created=True)
                headers = self.get_success_headers(data)

                task_url = Site.objects.get_current().domain + '/api/task?task_id=%s' %  str(result.id)

                return Response({"task":task_url}, status=status.HTTP_201_CREATED,
                                headers=headers)
            else:
                self.pre_save(serializer.object)
                data = serializer.restore_fields(request.DATA, request.FILES)

                databaseinfra = DatabaseInfra.best_for(data['plan'], data['environment'], data['name'])
                self.object = models.Database.provision(data['name'], databaseinfra)
                self.object.team = data['team']
                self.object.project = data['project']
                self.object.save()
                data = serializer.to_native(self.object)
                self.post_save(self.object, created=True)
                headers = self.get_success_headers(data)
                return Response(data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
