# -*- coding: utf-8 -*-
import logging
from util import exec_remote_command_host

LOG = logging.getLogger(__name__)


def use_database_initialization_script(databaseinfra, host, option):
    driver = databaseinfra.get_driver()
    initialization_script = driver.initialization_script_path(host)

    command = initialization_script.format(option=option)
    command += ' > /dev/null'

    output = {}
    return_code = exec_remote_command_host(host, command, output)
    return return_code, output
