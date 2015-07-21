# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceAPI, register
from .service.instance import InstanceService
from .service.databaseinfra import DatabaseInfraService
from .service.plan import PlanService
from .service.engine import EngineService, EngineTypeService
from .serializers import InstanceSerializer, DatabaseInfraSerializer, \
    EngineSerializer, EngineTypeSerializer, PlanSerializer


class EngineTypeAPI(DjangoServiceAPI):
    serializer_class = EngineTypeSerializer
    service_class = EngineTypeService


class EngineAPI(DjangoServiceAPI):
    serializer_class = EngineSerializer
    service_class = EngineService


class PlanAPI(DjangoServiceAPI):
    serializer_class = PlanSerializer
    service_class = PlanService


class DatabaseInfraAPI(DjangoServiceAPI):

    serializer_class = DatabaseInfraSerializer
    service_class = DatabaseInfraService
    operations = ('list', 'retrieve', 'create', 'update', 'destroy')


class InstanceAPI(DjangoServiceAPI):
    serializer_class = InstanceSerializer
    service_class = InstanceService


register('enginetype', EngineTypeAPI)
register('engine', EngineAPI)
register('plan', PlanAPI)
register('instance', InstanceAPI)
register('databaseinfra', DatabaseInfraAPI)
