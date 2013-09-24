# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import subprocess
import os.path
from django.utils.translation import ugettext_lazy as _
from ..models import Instance

# See http://docs.python.org/2/library/subprocess.html#popen-constructor if you
# have questions about this variable
DEFAULT_OUTPUT_BUFFER_SIZE = 4096

LOG = logging.getLogger(__name__)


class BaseEngine(object):
    """
    BaseEngine interface
    """
    ENV_CONNECTION = 'INSTANCE_CONNECTION'

    def __init__(self, *args, **kwargs):

        if 'instance' in kwargs:
            self.instance = kwargs.get('instance')
            self.node = self.instance.node
        else:
            raise TypeError(_("Instance is not defined"))

    def get_connection(self):
        """ Connection string passed to script as INSTANCE_CONNECTION environment variable. """
        raise NotImplementedError()

    def get_user(self):
        return self.instance.user

    def get_password(self):
        return self.instance.password

    def status(self):
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

    def get_script_path(self):
        """ Return PATH environment variable for this engine """

    def call_script(self, script_name, args=[], envs={}):
        working_dir = "./mongodb/scripts"
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
                envs_with_path = os.getenv("PATH")

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
            return_code = process.returncode

            if return_code != 0:
                raise RuntimeError("Error executing %s, exit code = %d: '%s'" % (script_name, return_code, output))
            return output
        except:
            # if any error happen, log cmdline to error
            LOG.error("Error running cmdline (exit code %s): %s", return_code, logging_cmdline, exc_info=True)
            raise

    def to_envs(self, obj):
        """ Create a dictionary with object variable, to be used as environment variables to script """

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
            envs[BaseEngine.ENV_CONNECTION] = self.get_connection()
        return envs

