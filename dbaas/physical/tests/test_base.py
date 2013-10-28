# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
from django.test import TestCase
from drivers import BaseDriver
from . import factory

CONNECTION_TEST = 'connection-url'

class FakeDriver(BaseDriver):
    
    def get_connection(self):
        return CONNECTION_TEST


class EngineTestCase(TestCase):
    """
    Tests Engine and EngineType
    """

    def setUp(self):
        self.databaseinfra = factory.DatabaseInfraFactory()
        self.engine = FakeDriver(databaseinfra=self.databaseinfra)

    def tearDown(self):
        self.databaseinfra.delete()
        self.databaseinfra = self.engine = None

    def test_to_envs_with_none_returns_empty_dict(self):
        self.assertEquals({}, self.engine.to_envs(None))

    def test_to_envs_with_databaseinfra_object_must_return_a_dictionary(self):
        self.assertEquals({
            'DATABASEINFRA_ID': str(self.databaseinfra.id),
            'DATABASEINFRA_NAME': self.databaseinfra.name,
            'DATABASEINFRA_PASSWORD': self.databaseinfra.password,
            'DATABASEINFRA_USER': self.databaseinfra.user,
            'DATABASEINFRA_CONNECTION': CONNECTION_TEST,
            }, self.engine.to_envs(self.databaseinfra))

    def test_call_script_will_put_engine_path_as_environment_variable(self):
        PATH = '/bin:/bin/path1:/bin/path2'
        self.engine.databaseinfra.engine.path = PATH
        result = self.engine.call_script("/bin/bash", ["-c", 'echo $PATH'])
        self.assertEquals(PATH, result.strip())

    def test_call_script_will_export_os_getenv_path_if_engine_path_is_not_set(self):
        PATH = os.getenv("PATH")
        result = self.engine.call_script("/bin/bash", ["-c", 'echo $PATH'])
        self.assertEquals(PATH, result.strip())
