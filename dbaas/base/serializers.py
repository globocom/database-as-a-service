from django_services.api import DjangoServiceSerializer
from rest_framework import serializers
from .models import Environment, Host, Instance, Database, Credential


class EnvironmentSerializer(DjangoServiceSerializer):

    class Meta:
        model = Environment


class HostSerializer(DjangoServiceSerializer):

    class Meta:
        model = Host


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


