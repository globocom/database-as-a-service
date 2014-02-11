# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from logical.models import Database
from logical.tests import factory
from physical.tests import factory as physical_factory
from . import DbaaSAPITestCase, BasicTestsMixin
LOG = logging.getLogger(__name__)


class DatabaseAPITestCase(DbaaSAPITestCase, BasicTestsMixin):
    model = Database
    url_prefix = 'database'

    def setUp(self):
        super(DatabaseAPITestCase, self).setUp()
        self.datainfra = physical_factory.DatabaseInfraFactory()
        self.instance = physical_factory.InstanceFactory(address="127.0.0.1", port=27017, databaseinfra=self.datainfra)

    def model_new(self):
        return factory.DatabaseFactory.build(databaseinfra=self.datainfra)

    def model_create(self):
        return factory.DatabaseFactory(databaseinfra=self.datainfra)

    def payload(self, database, **kwargs):
        data = {
            'name': database.name,
            'plan': reverse('plan-detail', kwargs={'pk': database.plan.pk }),
            'environment': reverse('environment-detail', kwargs={'pk': database.environment.pk }),
        }
        return data

    def test_delete(self):
        obj = self.model_create()
        url = self.url_detail(obj.pk)
        response = self.client.delete(url)

        # assert status code
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert if object gone
        self.assertRaises(ObjectDoesNotExist, Database.objects.filter(is_in_quarantine=False, pk=obj.pk).get)

