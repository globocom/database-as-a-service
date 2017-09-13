# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response
from dbaas.middleware import UserMiddleware
from logical import models
from physical.models import Plan, Environment
from account.models import Team
from .credential import CredentialSerializer
from django.contrib.sites.models import Site
from notification.tasks import TaskRegister
import logging

LOG = logging.getLogger(__name__)


class DatabaseSerializer(serializers.HyperlinkedModelSerializer):
    plan = serializers.HyperlinkedRelatedField(
        source='plan', view_name='plan-detail',
        queryset=Plan.objects.filter(is_active=True)
    )
    replication_topology_id = serializers.Field(source='databaseinfra.plan.replication_topology.id')
    environment = serializers.HyperlinkedRelatedField(
        source='environment', view_name='environment-detail',
        queryset=Environment.objects
    )
    team = serializers.HyperlinkedRelatedField(
        source='team', view_name='team-detail', queryset=Team.objects
    )
    endpoint = serializers.Field(source='endpoint')
    quarantine_dt = serializers.Field(source='quarantine_dt')
    total_size_in_bytes = serializers.Field(source='total_size')
    credentials = CredentialSerializer(many=True, read_only=True)
    status = serializers.Field(source='status')
    used_size_in_bytes = serializers.Field(source='used_size_in_bytes')
    engine = serializers.CharField(source='infra.engine', read_only=True)

    class Meta:
        model = models.Database
        fields = (
            'url', 'id', 'name', 'endpoint', 'plan', 'environment',
            'project', 'team', 'quarantine_dt', 'total_size_in_bytes',
            'credentials', 'description', 'status',
            'used_size_in_bytes', 'subscribe_to_email_events',
            'created_at', 'engine', 'replication_topology_id'
        )
        read_only = ('credentials', 'status', 'used_size_in_bytes')

    def __init__(self, *args, **kwargs):
        super(DatabaseSerializer, self).__init__(*args, **kwargs)

        request = self.context.get('request', None)
        if request:
            creating = request.method == 'POST'

            self.fields['plan'].read_only = not creating
            self.fields['environment'].read_only = not creating
            self.fields['name'].read_only = not creating
            self.fields['credentials'].read_only = True


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
                "description": "{description}",
                "subscribe_to_email_events": "{subscribe_to_email_events}",
                "contacts": "{contacts}"
            }
    *   ### __Show details about a database__
        __GET__ /api/database/`database_id`/
    *   ### __To delete a database (will put it on quarantine)__
        __DELETE__ /api/database/`database_id`/
    *   ### __To change database project__
        __PUT__ /api/database/`database_id`/
            {
                "project": "{api_url}/project/{project_id}/",
                "description": "{description}",
                "subscribe_to_email_events": "{subscribe_to_email_events}",
                "contacts": "{contacts}"
            }
    """
    serializer_class = DatabaseSerializer
    queryset = models.Database.objects.all()

    def create(self, request):
        serializer = self.get_serializer(
            data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            data = serializer.restore_fields(request.DATA, request.FILES)

            result = TaskRegister.database_create(
                name=data['name'], plan=data['plan'],
                environment=data['environment'], team=data['team'],
                project=data['project'], description=data['description'],
                subscribe_to_email_events=data['subscribe_to_email_events'],
                user=request.user,
                register_user=False
            )
            headers = self.get_success_headers(data)
            task_url = Site.objects.get_current().domain + \
                '/api/task?task_id=%s' % str(result.id)

            return Response(
                {"task": task_url}, status=status.HTTP_201_CREATED,
                headers=headers
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        UserMiddleware.set_current_user(request.user)

        if instance.is_in_quarantine or instance.is_protected:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
