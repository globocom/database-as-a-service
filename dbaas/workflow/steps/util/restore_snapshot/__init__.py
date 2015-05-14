# -*- coding: utf-8 -*-
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import exec_remote_command


def use_database_initialization_script(databaseinfra, host, option):
    driver = databaseinfra.get_driver()
    initialization_script = driver.initialization_script_path()

    command = initialization_script + ' ' + option + ' > /dev/null'

    cs_host_attr = CsHostAttr.objects.get(host=host)

    output = {}
    return_code = exec_remote_command(server=host.address,
                                      username=cs_host_attr.vm_user,
                                      password=cs_host_attr.vm_password,
                                      command=command,
                                      output=output)

    return return_code, output
