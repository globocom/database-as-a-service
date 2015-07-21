# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from logical.models import Project
from logical.tests import factory
from . import DbaaSAPITestCase, BasicTestsMixin
LOG = logging.getLogger(__name__)


class ProjectAPITestCase(DbaaSAPITestCase, BasicTestsMixin):
    model = Project
    url_prefix = 'project'

    def model_new(self):
        return factory.ProjectFactory.build()

    def model_create(self):
        return factory.ProjectFactory()

    def payload(self, test_obj, **kwargs):
        return {'name': "change-%s" % test_obj.name}
