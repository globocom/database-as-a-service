# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceSerializer
from .models import Node, Instance, Engine, EngineType, Plan


class EngineTypeSerializer(DjangoServiceSerializer):

    class Meta:
        model = EngineType


class EngineSerializer(DjangoServiceSerializer):

    class Meta:
        model = Engine


class PlanSerializer(DjangoServiceSerializer):

    class Meta:
        model = Plan


class InstanceSerializer(DjangoServiceSerializer):

    class Meta:
        model = Instance


class NodeSerializer(DjangoServiceSerializer):

    class Meta:
        model = Node
