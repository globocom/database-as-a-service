# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import link
from . import serializers
from .models import Database, Project, Credential
from rest_framework.response import Response
from drivers import factory_for


class ProjectAPI(viewsets.ModelViewSet):
    serializer_class = serializers.ProjectSerializer
    queryset = Project.objects.all()


class DatabaseAPI(viewsets.ModelViewSet):
    serializer_class = serializers.DatabaseSerializer
    queryset = Database.objects.all()

    @link()
    def status(self, request, pk):
        """ Status of DB """
        try:
            db = Database.objects.get(pk=pk)
            databaseinfra = db.databaseinfra
            factory_for(databaseinfra).check_status()
            return Response(
                {'status': 'WORKING'},
                status='200')
        except Database.DoesNotExist:
            return Response(
                {'status': 'Database does not exist.'},
                status='404')
        except Exception as e:
            return Response(
                {'status': 'Error. %s (%s)' % (e.message, type(e))},
                status='400')


class CredentialAPI(viewsets.ModelViewSet):
    serializer_class = serializers.CredentialSerializer
    queryset = Credential.objects.all()


register('project', ProjectAPI)
register('database', DatabaseAPI)
register('credential', CredentialAPI)

