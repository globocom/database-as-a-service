# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django_services import service
from ..models import Instance
from base.driver.factory import DriverFactory

LOG = logging.getLogger(__name__)


class InstanceService(service.CRUDService):
    model_class = Instance

    def __get_engine__(self, instance):
        return DriverFactory.factory(instance)

