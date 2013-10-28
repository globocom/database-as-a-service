# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceSerializer
from .models import Instance, DatabaseInfra, Engine, EngineType, Plan


class EngineTypeSerializer(DjangoServiceSerializer):

    class Meta:
        model = EngineType


class EngineSerializer(DjangoServiceSerializer):

    class Meta:
        model = Engine


class PlanSerializer(DjangoServiceSerializer):

    class Meta:
        model = Plan


class DatabaseInfraSerializer(DjangoServiceSerializer):

    class Meta:
        model = DatabaseInfra


class InstanceSerializer(DjangoServiceSerializer):

    class Meta:
        model = Instance
