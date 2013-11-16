# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from logical.models import Credential
from logical.tests import factory
from . import DbaaSAPITestCase, BasicTestsMixin
LOG = logging.getLogger(__name__)


class CredentialAPITestCase(DbaaSAPITestCase, BasicTestsMixin):
    model = Credential
    url_prefix = 'credential'

    def model_new(self):
        return factory.CredentialFactory.build()

    def model_create(self):
        return factory.CredentialFactory()

    def payload(self, test_obj, creation):
        return { 'user': "c-%s" % test_obj.user }
