# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from rest_framework import status
from logical.models import Credential
from logical.tests import factory
from django.core.urlresolvers import reverse
from . import DbaaSAPITestCase, BasicTestsMixin
# from util import make_db_random_password
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

    def payload(self, test_obj, listing=False, creation=False, **kwargs):
        data = {
            'user': test_obj.user,
            'database': reverse('database-detail', kwargs={'pk': test_obj.database.pk }),
            'password': test_obj.password,
        }
        if listing:
            del data['password']
        return data


    def test_post_on_reset_password(self):
        obj = self.model_create()
        url = "%sreset_password/" % self.url_detail(obj.pk)
        response = self.client.post(url, {}, content_type='application/json')
        data = response.data

        # assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.url_detail(obj.pk), response.data['_links']['self'])

        # check fields
        new_obj = Credential.objects.get(pk=obj.pk)
        self.assertNotEqual(new_obj.password, obj.password, 'Passwod not changed')
        self.assertEqual(new_obj.password, data['password'])
