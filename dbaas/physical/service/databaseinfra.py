# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django_services import service
from ..models import DatabaseInfra
from drivers import factory_for
from django_services.service import checkpermission

LOG = logging.getLogger(__name__)


class DatabaseInfraService(service.CRUDService):
    model_class = DatabaseInfra

    def __get_engine__(self, databaseinfra):
        return factory_for(databaseinfra)

    @checkpermission(prefix="view")
    def get_databaseinfra_status(self, databaseinfra):
        return self.__get_engine__(databaseinfra).info()
