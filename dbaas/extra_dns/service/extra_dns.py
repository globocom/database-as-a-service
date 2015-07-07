# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import service
from ..models import ExtraDns


class ExtraDnsService(service.CRUDService):
    model_class = ExtraDns

    def create(self, extra_dns):
        super(ExtraDnsService, self).create(extra_dns)

    def delete(self, extra_dns):
        super(ExtraDnsService, self).delete(extra_dns)
