# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
import os
from django.test import TestCase
from base.engine import base, ErrorRunningScript
from base.tests import factory

CONNECTION_TEST = 'connection-url'

class FakeEngine(base.BaseEngine):
    
    def get_connection(self):
        return CONNECTION_TEST


class EngineTestCase(TestCase):
    """
    Tests Engine and EngineType
    """

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.engine = FakeEngine(instance=self.instance)

    def tearDown(self):
        self.instance.delete()
        self.instance = self.engine = None

    def test_to_envs_with_none_returns_empty_dict(self):
        self.assertEquals({}, self.engine.to_envs(None))

    def test_to_envs_with_instance_object_must_return_a_dictionary(self):
        self.assertEquals({
            'INSTANCE_ID': str(self.instance.id),
            'INSTANCE_NAME': self.instance.name,
            'INSTANCE_PASSWORD': self.instance.password,
            'INSTANCE_USER': self.instance.user,
            'INSTANCE_CONNECTION': CONNECTION_TEST,
            }, self.engine.to_envs(self.instance))

    def test_call_script_will_put_engine_path_as_environment_variable(self):
        PATH = '/bin:/bin/path1:/bin/path2'
        self.engine.instance.engine.path = PATH
        result = self.engine.call_script("/bin/bash", ["-c", 'echo $PATH'])
        self.assertEquals(PATH, result.strip())

    def test_call_script_will_export_os_getenv_path_if_engine_path_is_not_set(self):
        PATH = os.getenv("PATH")
        result = self.engine.call_script("/bin/bash", ["-c", 'echo $PATH'])
        self.assertEquals(PATH, result.strip())

    @mock.patch.object(base.LOG, 'error')
    def test_when_script_exit_code_is_different_than_zero_raises_error_running_script(self, error_log):
        ERROR_MESSAGE = 'some error\n$#FOS!'
        EXIT_CODE = 5
        try:
            self.engine.call_script("/bin/bash", ["-c", "echo '%s'; exit %d" % (ERROR_MESSAGE, EXIT_CODE)])
            self.fail('Expected exception is not raised')
        except ErrorRunningScript, e:
            self.assertEquals(EXIT_CODE, e.exit_code)
            self.assertEquals(ERROR_MESSAGE, e.stdout)
            self.assertTrue(error_log.called, 'Error on execute script is not logged')

