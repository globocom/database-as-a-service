from base.engine import BaseEngine
import logging
import subprocess
import os.path

# ./MongoManager.sh 

# See http://docs.python.org/2/library/subprocess.html#popen-constructor if you
# have questions about this variable
DEFAULT_OUTPUT_BUFFER_SIZE = 4096

LOG = logging.getLogger(__name__)


class MongoDB(BaseEngine):

    def call_script(self, script_name, args=[], envs={}):
        working_dir = "./scripts"
        working_dir = os.path.abspath(working_dir)

        logging_cmdline = "%s %s %s" % (
            " ".join([ "%s=%s" % (k, "xxx" if k.endswith("_PASSWORD") else v) for (k,v) in envs.items()]),
            script_name,
            " ".join(args),
        )
        return_code = None
        try:
            LOG.info('Running on path %s command: %s', working_dir, logging_cmdline)

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
                env=envs,
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    envs = {
        'INSTANCE_NAME': 'localhost',
        'INSTANCE_CONNECTION': 'localhost:27017',
        'INSTANCE_USER': ' ',
        'INSTANCE_PASSWORD': ' ',
        'DATABASE_NAME': 'my_db',
        'CREDENTIALS_USER': 'my_usr',
        'CREDENTIALS_PASSWORD': 'blablalba',
    }
    output = MongoDB().call_script('./MongoManager.sh', args=['adduser'], envs=envs)
    print "output=", repr(output)

