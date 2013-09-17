from django_services.api import DjangoServiceSerializer
from rest_framework import serializers
from .models import Instance

class InstanceSerializer(DjangoServiceSerializer):
    uri = serializers.Field(source='uri')

    class Meta:
        model = Instance
        fields = ('name', 'port', 'uri')
