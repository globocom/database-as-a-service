# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from rest_framework import status
from logical.models import Credential
from logical.tests import factory
from django.core.urlresolvers import reverse
from . import DbaaSAPITestCase, BasicTestsMixin
from account.models import Role, Team

LOG = logging.getLogger(__name__)


class CredentialAPITestCase(DbaaSAPITestCase, BasicTestsMixin):
    model = Credential
    url_prefix = 'credential'

    def model_new(self):
        database = factory.DatabaseFactory()
        database.credentials.all().delete()  # delete previous credentials
        return factory.CredentialFactory.build(database=database)

    def model_create(self):
        database = factory.DatabaseFactory()
        database.credentials.all().delete()  # delete previous credentials
        return factory.CredentialFactory(database=database)

    def payload(self, test_obj, listing=False, creation=False, **kwargs):
        data = {
            'user': test_obj.user,
            'database': reverse('database-detail', kwargs={'pk': test_obj.database.pk}),
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

    def test_post_only_allow_you_create_credential_if_you_have_permission_on_datatabase(self):
        obj = self.model_new()

        # create new team
        self.role = Role.objects.get_or_create(name="other_role")[0]
        obj.database.team = Team.objects.get_or_create(name="other_team", role=self.role)[0]
        obj.database.save()

        url = "%s" % self.url_list()
        response = self.client.post(url, self.payload(obj, creation=True), content_type='application/json')

        # assert response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
