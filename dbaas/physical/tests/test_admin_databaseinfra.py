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
        self.user = User.objects.create_superuser(
            self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.engine = None
        self.client.logout()

    def test_user_pass_all_arguments_and_database_is_created(self):
        NUM_INSTANCES = 3
        databaseinfra_name = "test_new_database_infra"
        databaseinfra_user = "dbadmin"
        databaseinfra_pass = "123456"
        databaseinfra_endpoint = ""
        instance_port = 27017
        instance_dns = "my_instance_dns{}.com"
        params = {
            "name": databaseinfra_name,
            "user": databaseinfra_user,
            "password": databaseinfra_pass,
            "engine": self.engine.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "capacity": 1,
            "per_database_size_mbytes": 10,
            "instances-TOTAL_FORMS": NUM_INSTANCES,
            "instances-INITIAL_FORMS": 0,
            "instances-MAX_NUM_FORMS": NUM_INSTANCES,
            "cs_dbinfra_attributes-TOTAL_FORMS": 2,
            "cs_dbinfra_attributes-INITIAL_FORMS": 0,
            "cs_dbinfra_attributes-MAX_NUM_FORMS": 2,
            "cs_dbinfra_offering-TOTAL_FORMS": 1,
            "cs_dbinfra_offering-INITIAL_FORMS": 0,
            "cs_dbinfra_offering-MAX_NUM_FORMS": 1,

        }

        hosts = {}
        for i in xrange(NUM_INSTANCES):
            host = factory.HostFactory()
            hosts[host.pk] = host
            address = "10.10.1.%d" % host.pk
            instance_dns = instance_dns.format(host.pk)
            params["instances-%d-id" % i] = '',
            params["instances-%d-databaseinfra" % i] = '',
            params["instances-%d-hostname" % i] = host.pk,
            params["instances-%d-dns" % i] = instance_dns,
            params["instances-%d-address" % i] = address,
            params["instances-%d-port" % i] = instance_port,
            params["instances-%d-is_active" % i] = True,
            params["instances-%d-is_arbiter" % i] = False,
            params["instances-%d-instance_type" % i] = 2,

            if i == (NUM_INSTANCES - 1):
                databaseinfra_endpoint += "%s:%s" % (address, instance_port)
            else:
                databaseinfra_endpoint += "%s:%s," % (address, instance_port)

        params["endpoint"] = databaseinfra_endpoint
        params["endpoint_dns"] = databaseinfra_endpoint

        response = self.client.post(
            "/admin/physical/databaseinfra/add/", params)
        self.assertEqual(response.status_code, 302, response.content)
        # self.assertTrue(fake.database_created(self.databaseinfra.name, databaseinfra_name))

        databaseinfra = DatabaseInfra.objects.get(name=databaseinfra_name)
        self.assertEqual(databaseinfra_user, databaseinfra.user)
        self.assertEqual(databaseinfra_pass, databaseinfra.password)
        self.assertEqual(databaseinfra_endpoint, databaseinfra.endpoint)
        self.assertEqual(self.engine, databaseinfra.engine)
        self.assertEqual(self.plan, databaseinfra.plan)
        self.assertEqual(self.environment, databaseinfra.environment)
        self.assertEqual(NUM_INSTANCES, databaseinfra.instances.count())
        for instance in databaseinfra.instances.all():
            host = hosts[instance.hostname.pk]
            self.assertEqual(host, instance.hostname)
            self.assertEqual("10.10.1.%d" % host.pk, instance.address)
            self.assertEqual(instance_port, instance.port)
