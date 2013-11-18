# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from logical.models import Credential
from logical.tests import factory
from django.core.urlresolvers import reverse
from . import DbaaSAPITestCase, BasicTestsMixin
from util import make_db_random_password
LOG = logging.getLogger(__name__)


class CredentialAPITestCase(DbaaSAPITestCase, BasicTestsMixin):
    model = Credential
    url_prefix = 'credential'

    def model_new(self):
        database = factory.DatabaseFactory()
        database.credentials.all().delete() # delete previous credentials
        return factory.CredentialFactory.build(database=database)

    def model_create(self):
        database = factory.DatabaseFactory()
        database.credentials.all().delete() # delete previous credentials
        return factory.CredentialFactory(database=database)

    def payload(self, test_obj, creation):
        return {
            'user': test_obj.user,
            'database': reverse('database-detail', kwargs={'pk': test_obj.database.pk }),
            'password': make_db_random_password(),
        }
