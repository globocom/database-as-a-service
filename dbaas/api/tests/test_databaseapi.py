# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from datetime import datetime
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from logical.models import Database
from logical.tests import factory
from physical.tests import factory as physical_factory
from . import DbaaSAPITestCase, BasicTestsMixin
from mock import patch
from account.tests.factory import TeamFactory
from logical.tests.factory import ProjectFactory
LOG = logging.getLogger(__name__)


class DatabaseAPITestCase(DbaaSAPITestCase, BasicTestsMixin):
    model = Database
    url_prefix = 'database'

    def setUp(self):
        super(DatabaseAPITestCase, self).setUp()
        self.datainfra = physical_factory.DatabaseInfraFactory(
            engine__engine_type__name='mongodb'
        )
        self.instance = physical_factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=self.datainfra)
        self.team = TeamFactory()
        self.project = ProjectFactory()
        self.environment = self.datainfra.environment

    def model_new(self):
        return factory.DatabaseFactory.build(
            databaseinfra=self.datainfra, team=self.team, project=self.project,
            environment=self.environment
        )

    def model_create(self):
        return factory.DatabaseFactory(
            databaseinfra=self.datainfra,
            databaseinfra__engine__engine_type__name='mongodb'
        )

    @patch('notification.tasks.create_database.delay')
    def test_post_create_new(self, mock_delay):
        url = self.url_list()
        test_obj = self.model_new()
        payload = self.payload(test_obj, creation=True)
        response = self.client.post(url, payload, format='json')

        LOG.debug("Response: ".format(response))
        LOG.debug("Call args {}, Call count {}".format(
            mock_delay.call_args, mock_delay.call_count)
        )

        self.assertEquals(mock_delay.call_count, 1)
        call_args = mock_delay.call_args[1]

        self.assertEquals(test_obj.name, call_args['name'])
        self.assertEquals(test_obj.plan, call_args['plan'])
        self.assertEquals(test_obj.environment, call_args['environment'])
        self.assertEquals(test_obj.team, call_args['team'])
        self.assertEquals(test_obj.project, call_args['project'])
        self.assertEquals(test_obj.description, call_args['description'])

    def payload(self, database, **kwargs):
        data = {
            'name': database.name,
            'plan': reverse('plan-detail', kwargs={'pk': database.plan.pk}),
            'environment': reverse('environment-detail', kwargs={'pk': database.environment.pk}),
            'team': reverse('team-detail', kwargs={'pk': database.team.pk}),
            'project': reverse('project-detail', kwargs={'pk': database.project.pk}),
            'description': database.description,
        }
        return data

    def test_delete(self):
        obj = self.model_create()
        url = self.url_detail(obj.pk)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertRaises(
            ObjectDoesNotExist,
            Database.objects.filter(is_in_quarantine=False, pk=obj.pk).get
        )

        obj = self.model.objects.get(id=obj.pk)
        self.assertTrue(obj.is_in_quarantine)
        self.assertEqual(obj.quarantine_dt, datetime.now().date())
        self.assertEqual(obj.quarantine_user.username, self.USERNAME)
