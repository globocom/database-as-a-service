from unittest import TestCase
from mock import MagicMock, patch, PropertyMock

from paramiko.ssh_exception import (BadHostKeyException,
                                    AuthenticationException,
                                    SSHException)
from socket import error as socker_err
from physical.ssh import (HostSSH, connect_host,
                          PassAndPkeyEmptyException,
                          ScriptFailedException)


def make_fake_exec_command_output(*args, **kw):
    stdin = MagicMock()
    stdout = MagicMock()
    stderr = MagicMock()

    stdout.readlines.return_value = 'fake_stdout'
    stderr.readlines.return_value = ''
    stdout.channel.recv_exit_status.return_value = 0
    return stdin, stdout, stderr


def make_fake_err_exec_command_output(*args, **kw):
    stdin = MagicMock()
    stdout = MagicMock()
    stderr = MagicMock()

    stdout.readlines.return_value = 'error'
    stderr.readlines.return_value = 'fake stderr'
    stdout.channel.recv_exit_status.return_value = 88
    return stdin, stdout, stderr


class DecoratorConnectHostTestCase(TestCase):
    def setUp(self):
        self.host_ssh = HostSSH(
            address='fake_address',
            username='fake_username',
            password='fake_password'
        )
        self.fake_func = MagicMock(
            return_value={
                'stdout': 'fake_stdout',
                'stdin': 'fake_stdin',
                'stderr': 'fake_stderr',
                'exception': '',
            }
        )
        self.decorated = connect_host(self.fake_func)

    @patch.object(HostSSH, 'connect')
    def test_call_connect_when_not_error(self, connect_mock):
        output = self.decorated(self.host_ssh)

        self.assertTrue(connect_mock.called)
        self.assertTrue(self.fake_func.called)
        self.assertEqual(output['stdout'], 'fake_stdout')
        self.assertEqual(output['exception'], '')

    @patch.object(HostSSH, 'connect',
                  side_effect=BadHostKeyException(
                      'fake_hostname', MagicMock(), MagicMock()
                  ))
    def test_call_connect_bad_host_exception(self, connect_mock):
        output = self.decorated(self.host_ssh)

        self.assertTrue(connect_mock.called)
        self.assertFalse(self.fake_func.called)
        self.assertEqual(output['stdout'], '')
        self.assertIn(
            "fake_hostname",
            output['exception']
        )

    @patch.object(HostSSH, 'connect',
                  side_effect=SSHException(
                      'fake err msg'
                  ))
    def test_call_connect_ssh_exception(self, connect_mock):
        output = self.decorated(self.host_ssh)

        self.assertTrue(connect_mock.called)
        self.assertFalse(self.fake_func.called)
        self.assertEqual(output['stdout'], '')
        self.assertEqual(
            "fake err msg",
            output['exception']
        )

    @patch.object(HostSSH, 'connect',
                  side_effect=AuthenticationException(
                      'fake err msg'
                  ))
    def test_call_connect_auth_exception(self, connect_mock):
        output = self.decorated(self.host_ssh)

        self.assertTrue(connect_mock.called)
        self.assertFalse(self.fake_func.called)
        self.assertEqual(output['stdout'], '')
        self.assertEqual(
            "fake err msg",
            output['exception']
        )

    @patch.object(HostSSH, 'connect',
                  side_effect=socker_err(
                      'fake err msg'
                  ))
    def test_call_connect_socket_exception(self, connect_mock):
        output = self.decorated(self.host_ssh)

        self.assertTrue(connect_mock.called)
        self.assertFalse(self.fake_func.called)
        self.assertEqual(output['stdout'], '')
        self.assertEqual(
            "fake err msg",
            output['exception']
        )


class InitTestCase(TestCase):
    def test_raise_exception_if_dont_have_pass_and_pkey(self):
        with self.assertRaises(PassAndPkeyEmptyException):
            HostSSH(
                address='fake_addres',
                username='fake_username',
                password='',
                private_key=''
            )

    @patch.object(HostSSH, 'pkey',
                  new=PropertyMock(return_value='fake_pkey'))
    def test_set_auth_variable(self):
        ssh_host = HostSSH(
            address='fake_addres',
            username='fake_username',
            password='123',
            private_key=''
        )
        self.assertDictEqual(
            {
                'username': 'fake_username',
                'password': '123'
            },
            ssh_host.auth
        )
        ssh_host = HostSSH(
            address='fake_addres',
            username='fake_username',
            password='',
            private_key='fake_pkey'
        )
        self.assertDictEqual(
            {
                'username': 'fake_username',
                'pkey': 'fake_pkey'
            },
            ssh_host.auth
        )


@patch.object(HostSSH, 'connect',
              new=MagicMock())
class RunScriptTestCase(TestCase):
    def setUp(self):
        self.host_ssh = HostSSH(
            address='fake_address',
            username='fake_username',
            password='fake_pass'
        )
        self.host_ssh.connect = MagicMock()
        self.fake_client = PropertyMock()
        self.fake_client.exec_command.side_effect = (
            make_fake_exec_command_output
        )
        self.host_ssh.client = self.fake_client

    def test_script_run_with_success(self):
        output = self.host_ssh.run_script('fake command')
        self.assertTrue(self.host_ssh.client.exec_command.called)
        expected_output = {
            'stderr': '',
            'exception': '',
            'stdout': 'fake_stdout',
            'exit_code': 0
        }
        self.assertDictEqual(output, expected_output)

    def test_raise_error_if_status_code_differ_0(self):
        self.fake_client.exec_command.side_effect = (
            make_fake_err_exec_command_output
        )
        with self.assertRaises(ScriptFailedException):
            self.host_ssh.run_script(
                'fake command'
            )
        self.assertTrue(self.host_ssh.client.exec_command.called)

    def test_return_error_status_without_raise(self):
        self.fake_client.exec_command.side_effect = (
            make_fake_err_exec_command_output
        )
        output = self.host_ssh.run_script(
            'fake command',
            raise_if_error=False
        )
        self.assertTrue(self.host_ssh.client.exec_command.called)
        expected_output = {
            'stderr': 'fake stderr',
            'exception': '',
            'stdout': 'error',
            'exit_code': 88
        }
        self.assertDictEqual(output, expected_output)

    def test_raise_error_on_retry(self):
        self.fake_client.exec_command.side_effect = (
            make_fake_err_exec_command_output
        )
        with self.assertRaises(ScriptFailedException):
            self.host_ssh.run_script(
                'fake command',
                retry=True
            )
        self.assertEqual(self.host_ssh.client.exec_command.call_count, 2)

    def test_script_param(self):
        self.host_ssh.run_script('fake command')
        self.assertTrue(self.host_ssh.client.exec_command.called)
        script_arg = self.host_ssh.client.exec_command.call_args[0][0]
        self.assertEqual(
            script_arg,
            'sudo sh /tmp/{}'.format(self.host_ssh.script_file_name)
        )
