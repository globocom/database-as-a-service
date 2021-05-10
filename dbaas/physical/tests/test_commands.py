from unittest import TestCase
from model_mommy import mommy

from physical.commands import HostCommandOL6, HostCommandOL7


class CommandsBaseTestCase(object):
    OS_VERSION = ''
    HOST_COMMAND_CLASS = None
    EXPECTED_CMD_TMPL = ''

    def setUp(self):
        self.host = mommy.make(
            'Host',
            os_description='OL {}'.format(self.OS_VERSION)
        )
        self.instance = mommy.make('Instance', hostname=self.host)

    def test_is_instance(self):
        self.assertTrue(
            isinstance(self.host.commands, self.HOST_COMMAND_CLASS)
        )

    def test_start(self):
        cmd = self.host.commands.exec_service_command(
            service_name='fake_service_name',
            action='fake_start'
        )

        self.assertEqual(
            cmd,
            self.EXPECTED_CMD_TMPL.format(
                service_name='fake_service_name',
                action='fake_start'
            )
        )

    def test_stop(self):
        cmd = self.host.commands.exec_service_command(
            service_name='fake_service_name',
            action='fake_stop'
        )

        self.assertEqual(
            cmd,
            self.EXPECTED_CMD_TMPL.format(
                service_name='fake_service_name',
                action='fake_stop'
            )
        )

    def test_start_no_output(self):
        cmd = self.host.commands.exec_service_command(
            service_name='fake_service_name',
            action='fake_start',
            no_output=True
        )

        expected_cmd = '{} > /dev/null'.format(
            self.EXPECTED_CMD_TMPL.format(
                service_name='fake_service_name',
                action='fake_start'
            )
        )
        self.assertEqual(
            cmd,
            expected_cmd
        )

    def test_stop_no_output(self):
        cmd = self.host.commands.exec_service_command(
            service_name='fake_service_name',
            action='fake_stop',
            no_output=True
        )

        expected_cmd = '{} > /dev/null'.format(
            self.EXPECTED_CMD_TMPL.format(
                service_name='fake_service_name',
                action='fake_stop'
            )
        )
        self.assertEqual(
            cmd,
            expected_cmd
        )


class CustomCommandOL6TestCase(CommandsBaseTestCase, TestCase):
    OS_VERSION = '6.10'
    HOST_COMMAND_CLASS = HostCommandOL6
    EXPECTED_CMD_TMPL = '/etc/init.d/{service_name} {action}'


class CustomCommandOL7TestCase(CommandsBaseTestCase, TestCase):
    OS_VERSION = '7.10'
    HOST_COMMAND_CLASS = HostCommandOL7
    EXPECTED_CMD_TMPL = 'sudo systemctl {action} {service_name}.service'
