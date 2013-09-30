# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import service
from ..models import Engine, EngineType


class EngineService(service.CRUDService):
    model_class = Engine


class EngineTypeService(service.CRUDService):
    model_class = EngineType