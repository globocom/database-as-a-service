# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re
import logging
import json
from mock import patch, MagicMock
from rest_framework import test, status
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.urlresolvers import reverse
from account.models import Role, Team
from physical.models import Environment
from dbaas.tests.helpers import InstanceHelper

LOG = logging.getLogger(__name__)


def extract_pk_form_url(url):
    # when only pk was passed
    if url.isdigit():
        return int(url)

    # pk is always the last part of url
    m = re.match('^.*/(\d+)\/?$', url)
    if m:
        return int(m.group(1))
    return None


class DbaaSClient(test.APIClient):

    def request(self, **kwargs):
        # Ensure that any credentials set get added to every request.
        response = super(DbaaSClient, self).request(**kwargs)
        # convert data from json using rendered content
        if getattr(response, 'accepted_media_type', None) == 'application/json' and response.data:
            response.original_data = response.data
            response.data = json.loads(response.rendered_content)
        return response


class DbaaSAPITestCase(test.APITestCase):
    USERNAME = "test-ui-database"
    PASSWORD = "123456"
    client_class = DbaaSClient

    def setUp(self):
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.team = Team.objects.get_or_create(
            name="fake_team", role=self.role)[0]
        self.superuser = User.objects.create_superuser(
            self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.client.logout()


@patch('drivers.fake.FakeDriver.check_instance_is_master', new=MagicMock(side_effect=InstanceHelper.check_instance_is_master))
class BasicTestsMixin(object):
    SERVER_URL = "http://testserver"

    def url_detail(self, pk):
        return "%s%s" % (self.SERVER_URL, reverse('%s-detail' % self.url_prefix, kwargs={'pk': pk}))

    def url_list(self):
        return "%s%s" % (self.SERVER_URL, reverse('%s-list' % self.url_prefix))

    def model_get(self, pk):
        return self.model.objects.get(pk=pk)

    def model_new(self):
        raise NotImplementedError()

    def model_create(self):
        raise NotImplementedError()

    def payload(self, test_obj, **kwargs):
        raise NotImplementedError()

    def test_anonimous_user_can_not_have_access(self):
        self.client.logout()
        url = self.url_list()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_a_list_of_all_objecs_with_pagination(self):
        NUM_PAGES = 3
        NUM_OBJECTS = settings.REST_FRAMEWORK['PAGINATE_BY'] * NUM_PAGES
        for i in range(NUM_OBJECTS):
            self.model_create()

        next = self.url_list()
        pages = 0
        while next:
            pages += 1
            response = self.client.get(next)
            data = response.data
            self.assertEqual(
                self.model.objects.count(), data['_links']['count'])
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            for obj_data in data[self.url_prefix]:
                self.assertIsNotNone(obj_data['id'])
                obj = self.model_get(obj_data['id'])

                # check fields
                self.get_env(data)

                self.compare_object_and_dict(obj, obj_data, listing=True)
            next = data['_links']['next']
            # import pudb; pu.db
        self.assertEqual(NUM_PAGES, pages)

    def test_get(self):
        obj = self.model_create()
        url = self.url_detail(obj.pk)
        response = self.client.get(url)
        data = response.data
        self.get_env(data)

        # assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.url_detail(obj.pk), response.data['_links']['self'])

        # check fields
        self.compare_object_and_dict(obj, data)

    def compare_object_and_dict(self, test_obj, data, fields=None, **kwargs):
        if fields is None:
            fields = self.payload(test_obj, **kwargs).keys()

        for k in fields:
            if isinstance(data[k], basestring) and data[k].startswith(self.SERVER_URL):
                # extract id from url
                expected_value = extract_pk_form_url(data[k])
                value = getattr(getattr(test_obj, k), 'pk', None)
            else:
                expected_value = data[k]
                value = getattr(test_obj, k)
            LOG.info(
                'Comparing field %s: expected "%s" and found "%s"', k, expected_value, value)
            self.assertEqual(expected_value, value)

    def test_post_create_new(self):
        url = self.url_list()
        test_obj = self.model_new()
        payload = self.payload(test_obj, creation=True)
        response = self.client.post(url, payload, format='json')
        data = response.data

        # assert response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, data)

        self.assertEqual(
            self.url_detail(data['id']), data['_links']['self'], data)

        # assert object
        obj = self.model_get(data['id'])
        self.assertIsNotNone(obj)

        # check fields
        self.compare_object_and_dict(obj, data, fields=payload.keys())

    def test_delete(self):
        obj = self.model_create()
        url = self.url_detail(obj.pk)
        response = self.client.delete(url)

        # assert status code
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert if object gone
        self.assertRaises(ObjectDoesNotExist, self.model_get, obj.pk)

    def test_update(self):
        test_obj = self.model_create()
        url = self.url_detail(test_obj.pk)
        payload = self.payload(test_obj, creation=False)
        response = self.client.put(url, payload)
        data = response.data
        self.get_env(data)

        # assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(url, data['_links']['self'])

        # check fields
        obj = self.model_get(data['id'])
        self.compare_object_and_dict(obj, data)

    def get_env(self, data):
        if 'environment' in data:
            if isinstance(data['environment'], Environment):
                data['environment'] = data['environment'].name
