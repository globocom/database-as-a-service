# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import subprocess
import os.path
from django.utils.translation import ugettext_lazy as _
from physical.models import Instance
from django_services.service.exceptions import InternalException

# See http://docs.python.org/2/library/subprocess.html#popen-constructor if you
# have questions about this variable
DEFAULT_OUTPUT_BUFFER_SIZE = 16384

LOG = logging.getLogger(__name__)

__all__ = ['GenericDriverError', 'ErrorRunningScript', 'ConnectionError',
    'AuthenticationError', 'BaseDriver', 'DatabaseStatus', 'InstanceStatus']

class GenericDriverError(InternalException):
    """ Exception raises when any kind of problem happens when executing operations on instance """

    def __init__(self, message=None):
        self.message = message

    def __unicode__(self):
        return "%s: %s" % (type(self).__name__, self.message)

    def __str__(self):
        return b"%s: %s" % (type(self).__name__, self.message)

    def __repr__(self):
        return b"%s: %s" % (type(self).__name__, self.message)        


class ErrorRunningScript(GenericDriverError):
    """ Exception raise when same error happen running a command line script """

    def __init__(self, script_name, exit_code, stdout):
        self.exit_code = exit_code
        self.stdout = stdout
        self.script_name = script_name
        super(ErrorRunningScript, self).__init__(message='%s. Exit code=%s: stdout=%s' % (self.script_name, self.exit_code, self.stdout))

class ConnectionError(GenericDriverError):
    """ Raised when there is any problem to connect on instance """
    pass

class AuthenticationError(ConnectionError):
    """ Raised when there is any problem authenticating on instance """
    pass


class BaseDriver(object):
    """
    BaseDriver interface
    """
    ENV_CONNECTION = 'INSTANCE_CONNECTION'

    def __init__(self, *args, **kwargs):

        if 'instance' in kwargs:
            self.instance = kwargs.get('instance')
        else:
            raise TypeError(_("Instance is not defined"))

    def test_connection(self, credential=None):
        """ Tests the connection to the database """
        raise NotImplementedError()

    def get_connection(self):
        """ Connection string passed to script as INSTANCE_CONNECTION environment variable. """
        raise NotImplementedError()

    def get_user(self):
        return self.instance.user

    def get_password(self):
        return self.instance.password

    def check_status(self):
        """ Check if instance is working. If not working, raises subclass of GenericDriverError """
        raise NotImplementedError()

    def info(self):
        """ Returns a mapping with same attributes of instance """
        raise NotImplementedError()

    def create_user(self, credential):
        raise NotImplementedError()

    def remove_user(self, credential):
        raise NotImplementedError()

    def create_database(self, database):
        raise NotImplementedError()

    def remove_database(self, database):
        raise NotImplementedError()

    def list_databases(self):
        """list databases in a instance"""
        raise NotImplementedError()

    def import_databases(self, instance):
        """import databases already created in a instance"""
        raise NotImplementedError()

    def call_script(self, script_name, args=[], envs={}):
        working_dir = "./drivers/mongodb/scripts"
        working_dir = os.path.abspath(working_dir)

        logging_cmdline = "%s %s" % (
            " ".join([ "%s=%s" % (k, "xxx" if k.endswith("_PASSWORD") else v) for (k,v) in envs.items()]),
            " ".join([script_name] + args),
        )
        return_code = None
        try:
            LOG.info('Running on path %s command: %s', working_dir, logging_cmdline)

            if self.instance.engine.path:
                envs_with_path = {'PATH': self.instance.engine.path}
            else:
                envs_with_path = {'PATH': os.getenv("PATH")}

            if envs:
                envs_with_path.update(envs)

            # For future, if scripts have lot of output can be better
            # create a temporary file for stdout. Scripts with lot of output and subprocess.PIPE
            # can lock because this method not consume stdout without script finish execute.
            process = subprocess.Popen(
                [script_name] + args,
                bufsize=DEFAULT_OUTPUT_BUFFER_SIZE,
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # stderr and stdout are the same
                close_fds=True,
                cwd=working_dir,
                env=envs_with_path,
                universal_newlines=True)
            process.wait()

            output = process.stdout.read()
            if len(output) > 1 and output[-1] == '\n':
                # remove last end line
                output = output[:-1]

            return_code = process.returncode

            if return_code != 0:
                raise ErrorRunningScript(script_name, return_code, output)
            return output
        except:
            # if any error happen, log cmdline to error
            LOG.error("Error running cmdline (exit code %s): %s", return_code, logging_cmdline, exc_info=True)
            raise

    def to_envs(self, obj):
        """ Creates a dictionary with an object to be used as environment variables to script """

        if not obj:
            return {}

        obj_name = obj._meta.object_name.upper()

        envs = {}
        for field in obj._meta.fields:
            if field.name in ['created_at', 'updated_at'] or hasattr(field, 'related'):
                continue
            value = field.value_to_string(obj)
            envs["%s_%s" % (obj_name, field.name.upper())] = '' if value is None else str(value)

        if isinstance(obj, Instance):
            envs[BaseDriver.ENV_CONNECTION] = self.get_connection()
        return envs

class SizeUnitsMixin(object):

    @property
    def size_in_bytes(self):
        """ Size in bytes (long) """
        return self.__size

    @size_in_bytes.setter
    def size_in_bytes(self, size):
        try:
            self.__size = int(size)
        except TypeError:
            self.__size = -1

    @property
    def size_in_kbytes(self):
        """ Size in kbytes (float) """
        return self.size_in_bytes / 1024.

    @size_in_kbytes.setter
    def size_in_kbytes(self, size):
        self.size_in_bytes = size * 1024

    @property
    def size_in_mbytes(self):
        """ Size in megabytes (float) """
        return self.size_in_kbytes / 1024.

    @size_in_mbytes.setter
    def size_in_mbytes(self, size):
        self.size_in_kbytes = size * 1024

    @property
    def size_in_gbytes(self):
        """ Size in gigabytes (float) """
        return self.size_in_mbytes / 1024.

    @size_in_gbytes.setter
    def size_in_gbytes(self, size):
        self.size_in_mbytes = size * 1024

    @property
    def size_in_pbytes(self):
        """ Size in pentabytes (float) """
        return self.size_in_gbytes / 1024.

    @size_in_pbytes.setter
    def size_in_pbytes(self, size):
        self.size_in_gbytes = size * 1024


class DatabaseStatus(SizeUnitsMixin):

    def __init__(self, database_model):
        self.database_model = database_model
        self.size_in_bytes = -1

    @property
    def name(self):
        return self.database_model.name


class InstanceStatus(SizeUnitsMixin):

    def __init__(self, instance_model):
        self.instance_model = instance_model
        self.version = None
        self.size_in_bytes = -1
        self.databases_status = {}

    def get_database_status(self, database_name):
        """ Return DatabaseStatus of one specific database """
        return self.databases_status.get(database_name, None)

