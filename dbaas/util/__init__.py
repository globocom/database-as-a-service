# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from slugify import slugify as slugify_function
from django.contrib.auth.models import User
from django.http import HttpResponse
import json
import logging
import subprocess
import os

LOG = logging.getLogger(__name__)

# See http://docs.python.org/2/library/subprocess.html#popen-constructor if you
# have questions about this variable
DEFAULT_OUTPUT_BUFFER_SIZE = 16384

def slugify(string):
    return slugify_function(string, separator="_")

def make_db_random_password():
    return User.objects.make_random_password()

def as_json(f):
    def wrapper(request, *args, **kw):
        output = f(request, *args, **kw)
        if isinstance(output, HttpResponse):
            return output
        elif isinstance(output, basestring):
            return HttpResponse(output, content_type="text/plain")
        output = json.dumps(output, indent=4)
        return HttpResponse(output, content_type="application/json")
    return wrapper


def call_script(script_name, working_dir=None, split_lines=True, args=[], envs={}):
    # working_dir = "./mongodb/scripts"
    # working_dir = os.path.abspath(working_dir)
    if not working_dir:
        raise RuntimeError("Working dir is null")

    logging_cmdline = "%s %s" % (
        " ".join([ "%s=%s" % (k, "xxx" if k.endswith("_PASSWORD") else v) for (k,v) in envs.items()]),
        " ".join([script_name] + args),
    )
    return_code = None
    try:
        LOG.info('Running on path %s command: %s', working_dir, logging_cmdline)

        envs_with_path = {'PATH': os.getenv("PATH")}

        if envs:
            envs_with_path.update(envs)

        # For future, if scripts have lot of output can be better
        # create a temporary file for stdout. Scripts with lot of output and subprocess.PIPE
        # can lock because this method not consume stdout without script finish execute.
        process = subprocess.Popen(
            [working_dir + script_name] + args,
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
        if split_lines:
            return return_code, [s.strip() for s in output.splitlines()]
        else:
            return return_code, output
    except:
        # if any error happen, log cmdline to error
        LOG.error("Error running cmdline (exit code %s): %s", return_code, logging_cmdline, exc_info=True)
        if not return_code:
            return_code = 1
        return return_code, []