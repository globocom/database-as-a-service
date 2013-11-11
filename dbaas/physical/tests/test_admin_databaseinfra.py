# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from django.contrib.auth.models import User
# from drivers import fake
from ..models import DatabaseInfra
# from ..forms import DatabaseForm
from . import factory

LOG = logging.getLogger(__name__)


class AdminCreateDatabaseInfraTestCase(TestCase):
    """ HTTP test cases """
    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):
        self.engine = factory.EngineFactory()
        self.plan = factory.PlanFactory(engine_type=self.engine.engine_type)
        self.environment = self.plan.environments.all()[0]
        self.user = User.objects.create_superuser(self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.engine = None
        self.client.logout()

    def test_user_pass_all_arguments_and_database_is_created(self):
        NUM_INSTANCES = 3
        databaseinfra_name = "test_new_database_infra"
        databaseinfra_user = "dbadmin"
        databaseinfra_pass = "123456"
        instance_port = 27017
        params = {
            "name": databaseinfra_name,
            "user": databaseinfra_user,
            "password": databaseinfra_pass,
            "engine": self.engine.pk,
            "plan": self.plan.pk,
            "capacity": 1,
            "environment": self.environment.pk,
            "instances-TOTAL_FORMS": NUM_INSTANCES,
            "instances-INITIAL_FORMS": 0,
            "instances-MAX_NUM_FORMS": NUM_INSTANCES,
        }

        hosts = {}
        for i in xrange(NUM_INSTANCES):
            host = factory.HostFactory()
            hosts[host.pk] = host

            params["instances-%d-hostname" % i] = host.pk,
            params["instances-%d-address" % i] = "10.10.1.%d" % host.pk,
            params["instances-%d-port" % i] = instance_port,


        response = self.client.post("/admin/physical/databaseinfra/add/", params)
        self.assertEqual(response.status_code, 302, response.content)
        # self.assertTrue(fake.database_created(self.databaseinfra.name, databaseinfra_name))

        databaseinfra = DatabaseInfra.objects.get(name=databaseinfra_name)
        self.assertEqual(databaseinfra_user, databaseinfra.user)
        self.assertEqual(databaseinfra_pass, databaseinfra.password)
        self.assertEqual(self.engine, databaseinfra.engine)
        self.assertEqual(self.plan, databaseinfra.plan)
        self.assertEqual(self.environment, databaseinfra.environment)
        self.assertEqual(NUM_INSTANCES, databaseinfra.instances.count())
        for instance in databaseinfra.instances.all():
            host = hosts[instance.hostname.pk]
            self.assertEqual(host, instance.hostname)
            self.assertEqual("10.10.1.%d" % host.pk, instance.address)
            self.assertEqual(instance_port, instance.port)
