import socket
import logging
from time import sleep
from StringIO import StringIO
from uuid import uuid4
from io import BytesIO

import paramiko


LOG = logging.getLogger(__name__)


def connect_host(func):
    def wrapper(self, *args, **kw):
        try:
            self.connect()
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


class PassAndPkeyEmptyException(Exception):
    pass


class HostSSH(object):
    ScriptFailedException = ScriptFailedException

    def __init__(self, address, username, password=None, private_key=None):
        self.address = address
        self.private_key = private_key
        if self.private_key:
            self.private_key = self.private_key.replace('\\n', '\n')
        if not any([password, private_key]):
            raise PassAndPkeyEmptyException(
                "You need set password or private key"
            )
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
            'exception': '',
        }
        self.script_file_dir = ''
        self.script_file_name = ''
        self.script_file_full_path = ''

    def connect(self, timeout=None):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )
        self.client.connect(
            self.address,
            timeout=timeout,
            **self.auth
        )

    @property
    def pkey(self):
        return paramiko.RSAKey.from_private_key(
            StringIO(self.private_key)
        )

    def handle_command_output(self, command_output):
        stdin, stdout, stderr = command_output
        self.stdout = stdout.readlines()
        self.stderr = stderr.readlines()
        self.script_exit_code = stdout.channel.recv_exit_status()
        self.output.update({
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exception': '',
            'exit_code': self.script_exit_code
        })

    def clean_script_files(self):
        if self.script_file_full_path:
            ftp = self.client.open_sftp()
            try:
                ftp.remove(self.script_file_full_path)
            except IOError:
                pass
            ftp.close()

    def set_script_file_variables(self):
        self.script_file_name = '{}.sh'.format(uuid4())
        self.script_file_dir = '/tmp'
        self.script_file_full_path = '{}/{}'.format(
            self.script_file_dir,
            self.script_file_name
        )

    def create_script_file(self, script):
        self.set_script_file_variables()
        ftp = self.client.open_sftp()
        ftp.putfo(BytesIO(script.encode()), self.script_file_full_path)
        ftp.close()

    @property
    def run_script_file_command(self):
        return 'sudo sh {}'.format(
            self.script_file_full_path
        )

    @connect_host
    def run_script(self, script, get_pty=False, raise_if_error=True,
                   retry=False):
        self.create_script_file(script)
        LOG.info(
            "Executing command [{}] on remote server {}".format(
                script, self.address
            )
        )
        command_output = self.client.exec_command(
            self.run_script_file_command,
            get_pty=get_pty
        )
        self.handle_command_output(command_output)
        LOG.info(
            "Command output: [{}]".format(self.output)
        )
        self.clean_script_files()
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

    def check(self, retries=30, wait=30, interval=40, timeout=None):
        LOG.info(
            "Waiting {} seconds to check {} ssh connection...".format(
                wait, self.address
            )
        )
        sleep(wait)

        for attempt in range(retries):
            try:

                LOG.info(
                    "Login attempt number {} on {} ".format(
                        attempt + 1, self.address
                    )
                )

                self.connect(timeout=timeout)
                return True

            except (paramiko.ssh_exception.BadHostKeyException,
                    paramiko.ssh_exception.AuthenticationException,
                    paramiko.ssh_exception.SSHException,
                    socket.error) as err:

                if attempt == retries - 1:
                    LOG.error(
                        "Maximum number of login attempts : {} .".format(err)
                    )
                    return False

                LOG.warning("We caught an exception: {} .".format(err))
                sleep(interval)
