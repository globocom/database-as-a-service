# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django_services import service
from ..models import Instance
from drivers import factory
from django_services.service import checkpermission

LOG = logging.getLogger(__name__)


class InstanceService(service.CRUDService):
    model_class = Instance

    def __get_engine__(self, instance):
        return factory_for(instance)

    @checkpermission(prefix="view")
    def get_instance_status(self, instance):
        return self.__get_engine__(instance).info()
