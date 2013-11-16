# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
# from django.test.utils import override_settings
from rest_framework import status
from account.models import Role, Team
from logical.models import Project
from logical.tests import factory
from . import DbaaSAPITestCase
LOG = logging.getLogger(__name__)


class ProjectAPITestCase(DbaaSAPITestCase):
    """ HTTP test cases """
    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.team = Team.objects.get_or_create(name="fake_team", role=self.role)[0]
        self.superuser = User.objects.create_superuser(self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.team.users.add(self.superuser)
        # self.client = 
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.client.logout()

    def url_detail(self, pk):
        return "http://testserver%s" % reverse('project-detail', kwargs={'pk': pk})

    def url_list(self):
        return "http://testserver%s" % reverse('project-list')

    def model_new(self):
        return factory.ProjectFactory.build()

    def model_create(self):
        return factory.ProjectFactory()

    def model_get(self, pk):
        return Project.objects.get(pk=pk)

    def test_returns_a_list_of_all_projects_with_pagination(self):
        NUM_PAGES = 3
        NUM_OBJECTS = settings.REST_FRAMEWORK['PAGINATE_BY']*NUM_PAGES
        for i in range(NUM_OBJECTS):
            self.model_create()

        next = self.url_list()
        pages = 0
        while next:
            pages += 1
            response = self.client.get(next)
            data = response.data
            self.assertEqual(Project.objects.count(), data['_links']['count'])
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            for obj_data in data['project']:
                self.assertIsNotNone(obj_data['id'])
                obj = self.model_get(obj_data['id'])
                self.assertEqual(obj.name, obj_data['name'])
            next = data['_links']['next']
        self.assertEqual(NUM_PAGES, pages)


    def test_get(self):
        obj = self.model_create()
        url = self.url_detail(obj.pk)
        response = self.client.get(url)
        data = response.data

        # assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.url_detail(obj.pk), response.data['_links']['self'])
        self.assertEqual(data['name'], obj.name)

    def test_post_create_new(self):
        url = self.url_list()
        test_obj = self.model_new()
        payload = { 'name': "xx-%s" % test_obj.name }
        response = self.client.post(url, payload)
        data = response.data

        # assert response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.url_detail(data['id']), data['_links']['self'])

        # assert object
        obj = self.model_get(data['id'])
        self.assertIsNotNone(obj)
        self.assertEqual(data['name'], obj.name)

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
        payload = { 'name': test_obj.name }
        response = self.client.put(url, payload)
        data = response.data

        # assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(url, data['_links']['self'])
        self.assertEqual(payload['name'], data['name'])
        
        # check if database was update
        obj = self.model_get(data['id'])
        self.assertEqual(data['name'], obj.name)
