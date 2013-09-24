# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import service
from ..models import Engine


class EngineService(service.CRUDService):
    model_class = Engine
