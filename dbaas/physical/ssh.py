import socket
import logging
from StringIO import StringIO

import paramiko


LOG = logging.getLogger(__name__)


def connect_host(func):
    def wrapper(self, *args, **kw):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            self.client.connect(
                self.address,
                **self.auth
            )
            return func(self, *args, **kw)
        except (paramiko.ssh_exception.BadHostKeyException,
                paramiko.ssh_exception.AuthenticationException,
                paramiko.ssh_exception.SSHException,
                socket.error) as e:
            msg = "We caught an exception: {}.".format(e)
            LOG.warning(msg)
            self.output['exception'] = str(e)
            return self.output

    return wrapper


class ScriptFailedException(Exception):
    pass


class HostSSH(object):
    ScriptFailedException = ScriptFailedException

    def __init__(self, address, username, password=None, key=None):
        self.address = address
        self.key = key.replace('\\n', '\n') if key else None
        if not any([password, key]):
            raise Exception("You need set password or key")
        self.auth = {'username': username}
        if password:
            self.auth['password'] = password
        else:
            self.auth['pkey'] = self.pkey
        self.stdout = ''
        self.stdin = ''
        self.stderr = ''
        self.output = {
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exeption': '',
        }

    @property
    def pkey(self):
        return paramiko.RSAKey.from_private_key(
            StringIO(self.key)
        )

    def handle_command_output(self, command_output):
        stdin, stdout, stderr = command_output
        self.stdout = stdout.readlines()
        self.stderr = stderr.readlines()
        self.script_exit_code = stdout.channel.recv_exit_status()
        self.output.update({
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exeption': '',
            'exit_code': self.script_exit_code
        })

    @connect_host
    def run_script(self, script, get_pty=False, raise_if_error=True,
                   retry=False):
        LOG.info(
            "Executing command [{}] on remote server {}".format(
                script, self.address
            )
        )
        try:
            command_output = self.client.exec_command(
                script,
                get_pty=get_pty
            )
        except (paramiko.ssh_exception.BadHostKeyException,
                paramiko.ssh_exception.AuthenticationException,
                paramiko.ssh_exception.SSHException,
                socket.error) as e:
            msg = "We caught an exception: {}.".format(e)
            LOG.warning(msg)
            self.output['exception'] = str(e)
            return self.output
        self.handle_command_output(command_output)
        if self.script_exit_code != 0:
            if retry:
                return self.run_script(
                    script=script,
                    get_pty=get_pty,
                    raise_if_error=raise_if_error,
                    retry=False
                )
            elif raise_if_error:
                raise ScriptFailedException(
                    'Could not execute script with exit code {}: {}'.format(
                        self.script_exit_code, self.output
                    )
                )

        return self.output
