# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceSerializer
from rest_framework import serializers
from .models import Environment, Node, Instance, Database, Credential, Engine, EngineType


class EnvironmentSerializer(DjangoServiceSerializer):

    class Meta:
        model = Environment


class NodeSerializer(DjangoServiceSerializer):

    class Meta:
        model = Node


class InstanceSerializer(DjangoServiceSerializer):
    uri = serializers.Field(source='uri')

    class Meta:
        model = Instance
        fields = ('name', 'port', 'uri')


class DatabaseSerializer(DjangoServiceSerializer):

    class Meta:
        model = Database


class CredentialSerializer(DjangoServiceSerializer):

    class Meta:
        model = Credential


class EngineSerializer(DjangoServiceSerializer):

    class Meta:
        model = Engine


class EngineTypeSerializer(DjangoServiceSerializer):

    class Meta:
        model = EngineType

